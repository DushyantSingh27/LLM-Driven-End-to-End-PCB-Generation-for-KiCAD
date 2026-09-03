"""Role derivation against the real netlist and real footprint pad counts."""
import pcbnew
from netlist_reader import parse_netlist_nets_meta
from design_rules import build_rule_table
from grouping import parse_netlist_values
from roles import classify_components

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.net"
PCB = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\integrated_test.kicad_pcb"

b = pcbnew.LoadBoard(PCB)
pads = {f.GetReference(): f.GetPadCount() for f in b.GetFootprints()}
meta = parse_netlist_nets_meta(NET)
net_class, rules, prov = build_rule_table(meta)
vals = parse_netlist_values(NET)

r = classify_components(pads, meta, net_class, vals)
print("anchor:", r["anchor"], "| ICs:", r["ics"])
for role in sorted(r["by_role"]):
    print("  %-11s %s" % (role, r["by_role"][role]))
print("\nunclassified ('other'):", r["by_role"].get("other", []))
