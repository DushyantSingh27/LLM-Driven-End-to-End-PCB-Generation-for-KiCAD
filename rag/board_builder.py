"""board_builder.py - authoring primitives for .kicad_pcb via pcbnew (KiCad 9.0).
Runs under KiCad's bundled Windows python.exe. All paths passed to pcbnew must be
Windows-form (C:\\...); callers translate via `wslpath -w`. Verified API set:
CreateEmptyBoard, FootprintLoad(path,name), SetReference, SetPosition,
VECTOR2I(FromMM,FromMM), board.Add, Pads(), SaveBoard, LoadBoard.
"""
import pcbnew
from netlist_reader import parse_netlist_components, parse_netlist_nets

FP_BASE = "C:\\Program Files\\KiCad\\9.0\\share\\kicad\\footprints"


def new_board():
    """Return a fresh, empty, saveable BOARD."""
    return pcbnew.CreateEmptyBoard()


def place_footprint(board, lib, name, ref, x_mm, y_mm):
    """Load footprint <lib>/<name>, set its ref + position (mm), add to board.
    Returns the FOOTPRINT. Raises if the footprint fails to resolve."""
    path = FP_BASE + "\\" + lib
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError("FootprintLoad returned None for %s/%s" % (lib, name))
    fp.SetReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm)))
    board.Add(fp)
    return fp


def save_board(board, out_win_path):
    """Save board to a Windows-form path. Returns SaveBoard's rc."""
    if isinstance(board, str) or not isinstance(out_win_path, str):
        raise TypeError("save_board(board, path) - arguments look swapped")
    # KiCad 9 keeps NETCLASS DEFINITIONS in the .kicad_pro project file, not in
    # the .kicad_pcb - and SaveBoard does NOT overwrite an existing project
    # file. A stale .kicad_pro therefore silently overrides freshly computed
    # design rules (measured: a board rebuilt with 0.09 clearance loaded back
    # as 0.15 because its project file was three weeks old). Remove it so the
    # save regenerates it from the board's current settings.
    import os
    pro = out_win_path.rsplit(".", 1)[0] + ".kicad_pro"
    if os.path.exists(pro):
        os.remove(pro)
    return pcbnew.SaveBoard(out_win_path, board)


if __name__ == "__main__":
    # self-check: place one hard footprint, save, reload, confirm it survived
    import os
    OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\bb_selfcheck.kicad_pcb"
    b = new_board()
    fp = place_footprint(b, "Package_CSP.pretty", "ST_WLCSP-72_Die415", "U1", 100.0, 100.0)
    print("placed:", fp.GetReference(), "pads=", fp.GetPadCount())
    rc = save_board(b, OUT)
    print("save rc=", rc, "exists=", os.path.exists(OUT))
    b2 = pcbnew.LoadBoard(OUT)
    fps = b2.GetFootprints()
    print("reload: n=", len(fps), "ref=", fps[0].GetReference(), "pads=", fps[0].GetPadCount())
    print("SELFCHECK", "PASS" if (len(fps)==1 and fps[0].GetPadCount()==72) else "FAIL")



def place_all_grid(netlist_path, out_win_path, origin_mm=(50.0, 50.0),
                   pitch_mm=10.0, cols=6):
    """Stage-2 placement: put every netlist component on a dumb fixed-pitch
    grid (distinct positions only - NOT real placement). Returns (board, comps)."""
    comps = parse_netlist_components(netlist_path)
    board = new_board()
    for idx, (ref, lib, name) in enumerate(comps):
        x = origin_mm[0] + (idx % cols) * pitch_mm
        y = origin_mm[1] + (idx // cols) * pitch_mm
        place_footprint(board, lib, name, ref, x, y)
    rc = save_board(board, out_win_path)
    if not rc:
        raise RuntimeError("SaveBoard returned falsy rc")
    return board, comps



def bind_nets(board, nets):
    """Create every net on the board and bind each (ref, pin) node to its pad.
    Binds ALL pads sharing the pin name (multi-pad nets are legal in KiCad).
    Returns (nets_created, pads_bound). Fails loudly on unknown ref/pin."""
    import pcbnew
    by_ref = {}
    for fp in board.GetFootprints():
        by_ref[fp.GetReference()] = fp
    pads_bound = 0
    for netname, members in nets:
        net = pcbnew.NETINFO_ITEM(board, netname)
        board.Add(net)
        for ref, pin in members:
            fp = by_ref.get(ref)
            if fp is None:
                raise RuntimeError("net %s: unknown ref %s" % (netname, ref))
            hits = [p for p in fp.Pads() if p.GetName() == pin]
            if not hits:
                raise RuntimeError("net %s: %s has no pad named %r" % (netname, ref, pin))
            for p in hits:
                p.SetNet(net)
                pads_bound += 1
    return len(nets), pads_bound
