"""layout_pipeline.py - one-shot layout: netlist -> placed, legalized .kicad_pcb.
Runs ONLY under KiCad's Windows python.exe. Consolidates verified stages:
build+bind (2/3) -> setup (P0) -> place (P4) -> legalize (P5) -> save.
Usage: python.exe layout_pipeline.py <netlist.net> <out.kicad_pcb>   (C:\\ paths)"""
import sys
import pcbnew
from board_builder import place_all_grid, save_board
from netlist_reader import parse_netlist_nets
from board_builder import bind_nets
from board_setup import setup_board
from grouping import parse_netlist_values, assign_decaps
from placement_engine import place_all
from legalize import legalize, courtyard_rect
from netlist_reader import parse_netlist_nets_meta
from design_rules import build_rule_table, plane_candidates
from rules_apply import apply_rules
from zones import pour_planes


def run_layout(net_path, out_path):
    print(">>> [L1/7] Building board + placing footprints from netlist...")
    board, comps = place_all_grid(net_path, out_path)
    print("    components:", len(comps))

    print(">>> [L2/7] Binding nets...")
    nets = parse_netlist_nets(net_path)
    n_nets, n_pads = bind_nets(board, nets)
    print("    nets:", n_nets, "pads bound:", n_pads)

    print(">>> [L3/7] Board setup (stackup, outline, DFM floors)...")
    setup_board(board, outline_wh_mm=(25.0, 25.0))

    print(">>> [L4/7] Constructive placement...")
    asg = assign_decaps(nets, parse_netlist_values(net_path))
    place_all(board, asg)

    print(">>> [L5/7] Legalizing...")
    iters, moved = legalize(board)
    print("    legalized in", iters, "iterations,", len(moved), "parts nudged")

    print(">>> [L6/7] Design rules -> netclasses...")
    meta = parse_netlist_nets_meta(net_path)
    net_class, class_rules, prov = build_rule_table(meta)
    created, assigned, missing = apply_rules(board, net_class, class_rules)
    print("    classes:", created, "| nets assigned:", assigned,
          "| missing:", len(missing))
    for c in sorted(class_rules):
        print("      %-7s track=%.3f clear=%.3f  <- %s"
              % (c, class_rules[c]["track_mm"], class_rules[c]["clearance_mm"],
                 prov[c]["track_mm"]))

    # SEAM: ZONE_FILLER hard-crashes (C++ level, no Python traceback) on an
    # in-memory board - verified by probe_pour_inmem.py, and BuildConnectivity()
    # does NOT fix it. Pouring works on a LoadBoard'ed board (stage 8), so we
    # save and reload here. Netclasses, layer types and placement all persist
    # (verified), so nothing is lost across the seam.
    print("    [seam] saving + reloading before pour (filler needs a loaded board)")
    if not save_board(board, out_path):
        raise RuntimeError("SaveBoard failed before pour")
    board = pcbnew.LoadBoard(out_path)

    print(">>> [L7/7] Copper planes...")
    gnet, pnet = plane_candidates(net_class, meta)
    if gnet is None or pnet is None:
        raise RuntimeError("could not derive plane nets: gnd=%r pwr=%r" % (gnet, pnet))
    planes = [(pcbnew.In1_Cu, gnet), (pcbnew.In2_Cu, pnet)]
    print("    derived planes: In1=%s  In2=%s" % (gnet, pnet))
    for name, layer, area in pour_planes(board, (20.0, 20.0, 45.0, 45.0), planes):
        print("      poured %-10s layer %d" % (name, layer))
    if not save_board(board, out_path):
        raise RuntimeError("SaveBoard failed")

    b2 = pcbnew.LoadBoard(out_path)
    n = len(b2.GetFootprints())
    if n != len(comps):
        raise RuntimeError("reload check: %d footprints, expected %d" % (n, len(comps)))
    print("    reload check OK:", n, "footprints")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    run_layout(sys.argv[1], sys.argv[2])
    print("LAYOUT OK:", sys.argv[2])
