"""Stage-12: import routed SES, refill zones (copper must wrap new tracks/vias),
save, and report the final board state."""
import pcbnew
from board_builder import save_board
from netlist_reader import parse_netlist_nets_meta
from design_rules import build_rule_table, plane_candidates
from zones import pour_planes

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage11_stitched.kicad_pcb"
SES = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage11_stitched.ses"
NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage12_final.kicad_pcb"

b = pcbnew.LoadBoard(SRC)
before = [len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]),
          len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T])]
print("before import -> tracks:", before[0], "vias:", before[1])

print("import rc:", pcbnew.ImportSpecctraSES(b, SES))
tr = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vi = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
print("after import  -> tracks:", len(tr), "vias:", len(vi))

# stitched copper must survive the import
if len(tr) < before[0] or len(vi) < before[1]:
    print("!!! WARNING: import REMOVED pre-existing stitching")

print("refilling zones so copper wraps the routed copper...")
meta = parse_netlist_nets_meta(NET)
net_class, rules, prov = build_rule_table(meta)
gnet, pnet = plane_candidates(net_class, meta)
for name, layer, area in pour_planes(b, (20.0, 20.0, 45.0, 45.0),
                                     [(pcbnew.In1_Cu, gnet), (pcbnew.In2_Cu, pnet)]):
    print("   poured", name, "layer", layer)
assert save_board(b, OUT)

b2 = pcbnew.LoadBoard(OUT)
print("=== final board ===")
print(" footprints:", len(b2.GetFootprints()),
      "| tracks:", len([t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]),
      "| vias:", len([t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]),
      "| zones:", len(list(b2.Zones())))
