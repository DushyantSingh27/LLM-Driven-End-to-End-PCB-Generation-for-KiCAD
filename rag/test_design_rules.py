from design_rules import (ipc2221_width_mm, classify_nets, build_rule_table)

print("=== IPC-2221 sanity check (external, 1oz, dT=10C) ===")
for i in (0.05, 0.1, 0.5, 1.0, 2.0, 5.0):
    w = ipc2221_width_mm(i)
    print("  %5.2f A -> %6.3f mm (%5.1f mil)" % (i, w, w/0.0254))
print("  cross-checked: 10mil external carries ~0.9A; internal ~2.6x external")

print("\n=== classification on real benchmark structure ===")
# mirrors the actual joined_e2e.net (pintypes verified compound with '+')
nets = {
 "/BOOT0":    [("R2","1",None,"passive"), ("U1","A7","BOOT0","input")],
 "/SPI_SCK":  [("U1","A6","PB3","bidirectional"), ("U2","13","SCL","input")],
 "/IMU_INT1": [("R3","2",None,"passive"), ("U1","E8","PB6","bidirectional"),
               ("U2","4","INT1","output")],
 "/VBAT":     [("C3","1",None,"passive"), ("U1","B9","VBAT","power_in")],
 "/VDD_3V3":  [("C7","1",None,"passive"), ("U1","A9","VDD","power_in"),
               ("U2","5","VDDIO","power_in")],
 "/VDD12":    [("C15","1",None,"passive"), ("U1","B8","VDD12","power_in")],
 "/VDDIO2":   [("C5","1",None,"passive"), ("U1","B6","VDDIO2","power_in")],
 "/VDDUSB":   [("C6","1",None,"passive"), ("U1","A1","VDDUSB","power_in")],
 "VDDA":      [("C4","1",None,"passive"), ("U1","H9","VDDA","power_in")],
 "/VREF_PLUS":[("C2","1",None,"passive"), ("U1","G8","VREF+","power_in")],
 "GND":       [("U1","A8","VSS","power_in"), ("U1","G9","VSSA","power_in"),
               ("U2","6","GND","power_in"), ("C1","2",None,"passive")],
 "unconnected-(U1-PA0-PadG5)": [("U1","G5","PA0","bidirectional+no_connect")],
}
cls = classify_nets(nets)
for n in sorted(cls): print("  %-30s %s" % (n, cls[n]))

print("\n=== GLM-style net names (different naming, same semantics) ===")
glm = {
 "VSS": [("U1","A8","VSS","power_in"), ("C1","2",None,"passive")],
 "VDD": [("U1","A9","VDD","power_in")],
 "VREF+": [("U1","G8","VREF+","power_in")],
 "SPI_SCK": [("U1","H5","PA5","bidirectional")],
}
for n, c in sorted(classify_nets(glm).items()): print("  %-10s %s" % (n, c))

print("\n=== resolved rule table (no current data supplied) ===")
nc, rules, prov = build_rule_table(nets)
for c in sorted(rules):
    print(" ", c, rules[c])
    for k, v in sorted(prov[c].items()): print("      %-14s <- %s" % (k, v))

print("\n=== with a supplied current on the main rail (0.8A) ===")
nc2, rules2, prov2 = build_rule_table(nets, currents={"/VDD_3V3": 0.8})
print("  POWER:", rules2["POWER"], "|", prov2["POWER"]["track_mm"])
