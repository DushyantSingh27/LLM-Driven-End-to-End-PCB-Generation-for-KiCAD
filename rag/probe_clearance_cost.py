"""Measure what CLASS_MIN_CLEARANCE_MM['POWER'] actually costs.
Runs stitching at several clearance values; reports stitched/unstitched each.
No board is modified - each run is on a fresh load."""
import pcbnew, copy
from netlist_reader import parse_netlist_nets_meta
from design_rules import build_rule_table, plane_candidates
from via_stitch import stitch_planes

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\integrated_test.kicad_pcb"
NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.net"

meta = parse_netlist_nets_meta(NET)
net_class, class_rules, prov = build_rule_table(meta)
gnet, pnet = plane_candidates(net_class, meta)

print("%-10s %-9s %-11s %s" % ("clearance", "stitched", "unstitched", "which"))
for clr in (0.09, 0.10, 0.115, 0.125, 0.15):
    rules = {n: dict(class_rules[c]) for n, c in net_class.items()}
    for n in rules:
        rules[n]["clearance_mm"] = clr
    b = pcbnew.LoadBoard(SRC)
    st, un = stitch_planes(b, {gnet, pnet}, (20.0, 20.0, 45.0, 45.0), rules)
    print("%-10.3f %-9d %-11d %s"
          % (clr, len(st), len(un), ", ".join("%s-%s" % (r, p) for r, p, _ in un)))
