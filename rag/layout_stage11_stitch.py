"""Stage-11: stitch plane pads to their planes, re-pour, report what failed."""
import pcbnew, collections
from board_builder import save_board
from netlist_reader import parse_netlist_nets_meta
from design_rules import build_rule_table, plane_candidates
from via_stitch import stitch_planes
from zones import pour_planes

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\integrated_test.kicad_pcb"
NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage11_stitched.kicad_pcb"

meta = parse_netlist_nets_meta(NET)
net_class, rules, prov = build_rule_table(meta)
gnet, pnet = plane_candidates(net_class, meta)
print("plane nets:", gnet, pnet)

board = pcbnew.LoadBoard(SRC)
net_rules = {n: rules[c] for n, c in net_class.items()}
print("rules: %s clearance=%.3f | %s clearance=%.3f"
      % (gnet, net_rules[gnet]["clearance_mm"], pnet, net_rules[pnet]["clearance_mm"]))
stitched, unstitched = stitch_planes(board, {gnet, pnet},
                                     (20.0, 20.0, 45.0, 45.0), net_rules)
print("stitched: %d   unstitched: %d" % (len(stitched), len(unstitched)))
print("=== UNSTITCHED (the honest list) ===")
by_ref = collections.Counter(r for r, _, _ in unstitched)
for ref, pad, net in unstitched:
    print("   %-4s pad %-4s %s" % (ref, pad, net))
print("   by component:", dict(by_ref))

print("=== re-pour so copper wraps the new vias ===")
planes = [(pcbnew.In1_Cu, gnet), (pcbnew.In2_Cu, pnet)]
for name, layer, area in pour_planes(board, (20.0, 20.0, 45.0, 45.0), planes):
    print("   poured", name, "layer", layer)
assert save_board(board, OUT)

b2 = pcbnew.LoadBoard(OUT)
vias = [t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
trks = [t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
print("after reload -> vias:", len(vias), "| tracks:", len(trks),
      "| zones:", len(list(b2.Zones())))
