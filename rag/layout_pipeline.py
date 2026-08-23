"""layout_pipeline.py - netlist in, routed board out, one call, no GUI.

Runs ONLY under KiCad's bundled Windows python.exe.
Usage: python.exe layout_pipeline.py <netlist.net> <run_dir>

Every artifact lands in <run_dir>, which the caller creates fresh (see
run_context.py). Reusing a directory is unsafe: KiCad 9 stores netclass
DEFINITIONS in the .kicad_pro and SaveBoard will not overwrite an existing
one, so a leftover project file silently overrides freshly computed rules.

Failure policy: routing is allowed to fail. A placed, poured, DRC-checked
board is still delivered, the failure is named in the report, and the exit
code distinguishes the cases. Nothing is ever silently skipped.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pcbnew

from board_builder import place_all_grid, bind_nets, save_board
from netlist_reader import parse_netlist_nets, parse_netlist_nets_meta
from board_setup import setup_board
from grouping import parse_netlist_values, assign_decaps
from placement_engine import place_all, POLICY
from legalize import legalize
from design_rules import (build_rule_table, plane_candidates,
                          router_clearance_mm, FAB_PROFILE_PCBPOWER)
from rules_apply import apply_rules
from via_stitch import stitch_planes, STITCH_POLICY
from zones import pour_planes
from routing import export_dsn, run_freerouting, import_ses

BOUNDS = POLICY["board"]


def say(*a):
    print(*a, flush=True)


def find_kicad_cli():
    exe = shutil.which("kicad-cli") or shutil.which("kicad-cli.exe")
    if exe:
        return exe
    default = "C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe"
    if os.path.exists(default):
        return default
    raise RuntimeError("kicad-cli not found on PATH or at %r" % default)


def run_drc(pcb_path, rpt_path):
    """Returns (counts_by_type, unconnected, raw_text)."""
    subprocess.run([find_kicad_cli(), "pcb", "drc",
                    "--output", rpt_path, pcb_path],
                   capture_output=True, text=True, timeout=600)
    txt = open(rpt_path, encoding="utf-8", errors="replace").read()
    counts = {}
    for kind in re.findall(r"^\[([a-z_]+)\]", txt, re.M):
        counts[kind] = counts.get(kind, 0) + 1
    unconn = counts.pop("unconnected_items", 0)
    return counts, unconn, txt


def run_layout(net_path, run_dir):
    art = lambda n: os.path.join(run_dir, n)
    board_path = art("board.kicad_pcb")
    report = {"netlist": net_path, "run_dir": run_dir, "stages": {}}

    say(">>> [L1/12] Footprints from netlist")
    board, comps = place_all_grid(net_path, board_path)
    report["stages"]["components"] = len(comps)
    say("    components:", len(comps))

    say(">>> [L2/12] Net binding")
    nets = parse_netlist_nets(net_path)
    n_nets, n_pads = bind_nets(board, nets)
    report["stages"]["nets"] = n_nets
    report["stages"]["pads_bound"] = n_pads
    say("    nets:", n_nets, "pads:", n_pads)

    say(">>> [L3/12] Board setup")
    setup_board(board, outline_wh_mm=(BOUNDS[2] - BOUNDS[0],
                                      BOUNDS[3] - BOUNDS[1]))

    say(">>> [L4/12] Constructive placement")
    meta = parse_netlist_nets_meta(net_path)
    asg = assign_decaps(nets, parse_netlist_values(net_path))
    place_all(board, asg)

    say(">>> [L5/12] Legalization")
    iters, moved = legalize(board)
    report["stages"]["legalize_iterations"] = iters
    say("    converged in", iters, "iterations")

    say(">>> [L6/12] Design rules")
    net_class, class_rules, prov = build_rule_table(meta)
    created, assigned, missing = apply_rules(board, net_class, class_rules)
    report["stages"]["netclasses"] = {c: class_rules[c] for c in class_rules}
    report["stages"]["rule_provenance"] = {c: prov[c] for c in prov}
    if missing:
        raise RuntimeError("nets not found on board: %s" % missing[:5])
    say("    classes:", created, "| nets assigned:", assigned)

    # SEAM: the zone filler hard-crashes on an in-memory board (C++ level, no
    # traceback) and BuildConnectivity does not help. Pouring works on a
    # LoadBoard'ed board, so we serialise here.
    say("    [seam] save + reload before pour")
    if not save_board(board, board_path):
        raise RuntimeError("SaveBoard failed before pour")
    board = pcbnew.LoadBoard(board_path)

    say(">>> [L7/12] Via stitching")
    gnet, pnet = plane_candidates(net_class, meta)
    if not gnet or not pnet:
        raise RuntimeError("could not derive plane nets: gnd=%r pwr=%r"
                           % (gnet, pnet))
    net_rules = {n: class_rules[c] for n, c in net_class.items()}
    stitched, unstitched = stitch_planes(board, {gnet, pnet}, BOUNDS, net_rules)
    report["stages"]["stitched"] = len(stitched)
    report["stages"]["unstitched"] = [list(u) for u in unstitched]
    say("    stitched:", len(stitched), "| unstitched:", len(unstitched))
    for ref, pad, net in unstitched:
        say("      UNREACHABLE %s pad %s (%s)" % (ref, pad, net))

    say(">>> [L8/12] Copper planes")
    planes = [(pcbnew.In1_Cu, gnet), (pcbnew.In2_Cu, pnet)]
    for name, layer, area in pour_planes(board, BOUNDS, planes):
        say("      poured %s on layer %d" % (name, layer))
    report["stages"]["planes"] = {"In1": gnet, "In2": pnet}
    if not save_board(board, board_path):
        raise RuntimeError("SaveBoard failed after pour")

    say(">>> [L9/12] DSN export")
    rclr = router_clearance_mm(
        min(r["clearance_mm"] for r in class_rules.values()),
        STITCH_POLICY["hole_clearance_mm"],
        FAB_PROFILE_PCBPOWER["min_drill_mm"],
        min(r["via_dia_mm"] for r in class_rules.values()))
    say("    router clearance: %.4f mm (derived so copper binds before holes)"
        % rclr)
    export_dsn(board, art("board.dsn"), router_clearance_mm=rclr)
    report["stages"]["router_clearance_mm"] = round(rclr, 4)

    say(">>> [L10/12] Autorouting")
    routed_ok, stats, log = run_freerouting(art("board.dsn"), art("board.ses"),
                                            exclude_nets=(gnet,))
    open(art("router.log"), "w", encoding="utf-8").write(log)
    report["stages"]["router"] = {k: v for k, v in stats.items()
                                  if k != "warnings"}
    say("    router ok:", routed_ok, "| unrouted:", stats.get("final_unrouted"))

    if routed_ok:
        say(">>> [L11/12] SES import + re-pour")
        t, v = import_ses(board, art("board.ses"))
        for name, layer, area in pour_planes(board, BOUNDS, planes):
            pass
        say("    traces:", t, "| vias:", v)
        report["stages"]["traces"] = t
        report["stages"]["vias"] = v
        if not save_board(board, board_path):
            raise RuntimeError("SaveBoard failed after routing")
    else:
        say("!!! [L11/12] ROUTING FAILED - delivering the placed board")
        report["stages"]["router_error"] = stats.get("error", "see router.log")

    say(">>> [L12/12] DRC")
    counts, unconn, _ = run_drc(board_path, art("drc.rpt"))
    report["drc"] = {"violations_by_type": counts, "unconnected": unconn}
    errors = sum(v for k, v in counts.items() if not k.startswith("silk"))
    report["result"] = {
        "board": board_path,
        "routed": routed_ok,
        "unconnected": unconn,
        "copper_violations": errors,
        "silk_warnings": sum(v for k, v in counts.items() if k.startswith("silk")),
        "clean": (routed_ok and unconn == 0 and errors == 0),
    }
    say("    unconnected:", unconn, "| copper violations:", errors,
        "| silk warnings:", report["result"]["silk_warnings"])

    with open(art("report.json"), "w") as f:
        json.dump(report, f, indent=2)

    say("=== %s ===" % ("PASS" if report["result"]["clean"] else "INCOMPLETE"))
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    rep = run_layout(sys.argv[1], sys.argv[2])
    sys.exit(0 if rep["result"]["clean"] else 1)
