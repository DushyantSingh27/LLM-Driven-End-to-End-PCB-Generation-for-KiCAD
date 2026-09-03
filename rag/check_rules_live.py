from netlist_reader import parse_netlist_nets_meta
from design_rules import build_rule_table, CLASS_MIN_CLEARANCE_MM
print("CLASS_MIN_CLEARANCE_MM as imported:", CLASS_MIN_CLEARANCE_MM)
meta = parse_netlist_nets_meta("/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs/joined_e2e/joined_e2e.net")
nc, rules, prov = build_rule_table(meta)
for c in sorted(rules):
    print("  %-7s clearance=%.3f" % (c, rules[c]["clearance_mm"]))
