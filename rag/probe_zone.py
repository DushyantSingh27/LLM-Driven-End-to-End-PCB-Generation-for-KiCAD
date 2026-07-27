"""Probe: pcbnew 9.0 ZONE authoring surface (create, outline, net, thermals, fill)."""
import pcbnew

B = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.kicad_pcb"
b = pcbnew.LoadBoard(B)

print("=== layer ids ===")
for n in ("F_Cu", "In1_Cu", "In2_Cu", "B_Cu"):
    print(" ", n, getattr(pcbnew, n, "MISSING"))

print("=== module-level zone symbols ===")
print(" filler:", [s for s in dir(pcbnew) if "FILLER" in s.upper()])
print(" connection enums:", [s for s in dir(pcbnew) if "ZONE_CONNECTION" in s][:8])
print(" fill modes:", [s for s in dir(pcbnew) if s.startswith("ZONE_FILL") or "ZFM_" in s][:8])

z = pcbnew.ZONE(b)
print("=== ZONE methods present? ===")
for n in ("SetLayer", "SetLayerSet", "SetNet", "SetNetCode", "Outline", "AddPolygon",
          "SetIsFilled", "SetPadConnection", "SetThermalReliefGap",
          "SetThermalReliefSpokeWidth", "SetLocalClearance", "SetMinThickness",
          "SetAssignedPriority", "SetPriority", "SetFillMode", "HatchBorder"):
    print("  %-28s %s" % (n, hasattr(z, n)))

o = z.Outline()
print("=== outline object ===")
print(" type:", type(o).__name__)
print(" methods:", [s for s in ("NewOutline", "Append", "AddOutline", "OutlineCount") if hasattr(o, s)])

print("=== existing zones on this board ===", len(list(b.Zones())))
