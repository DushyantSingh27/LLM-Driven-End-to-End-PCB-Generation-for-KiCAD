"""board_builder.py - authoring primitives for .kicad_pcb via pcbnew (KiCad 9.0).
Runs under KiCad's bundled Windows python.exe. All paths passed to pcbnew must be
Windows-form (C:\\...); callers translate via `wslpath -w`. Verified API set:
CreateEmptyBoard, FootprintLoad(path,name), SetReference, SetPosition,
VECTOR2I(FromMM,FromMM), board.Add, Pads(), SaveBoard, LoadBoard.
"""
import pcbnew

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
