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


def run_layout(net_path, out_path):
    print(">>> [L1/5] Building board + placing footprints from netlist...")
    board, comps = place_all_grid(net_path, out_path)
    print("    components:", len(comps))

    print(">>> [L2/5] Binding nets...")
    nets = parse_netlist_nets(net_path)
    n_nets, n_pads = bind_nets(board, nets)
    print("    nets:", n_nets, "pads bound:", n_pads)

    print(">>> [L3/5] Board setup (stackup, outline, DFM floors)...")
    setup_board(board, outline_wh_mm=(25.0, 25.0))

    print(">>> [L4/5] Constructive placement...")
    asg = assign_decaps(nets, parse_netlist_values(net_path))
    place_all(board, asg)

    print(">>> [L5/5] Legalizing + saving...")
    iters, moved = legalize(board)
    print("    legalized in", iters, "iterations,", len(moved), "parts nudged")
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
