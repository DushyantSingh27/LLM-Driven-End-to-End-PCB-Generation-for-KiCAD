"""Probe: can we mark In1/In2 as POWER PLANE layers via the 9.0 Python API?
Decides whether board_setup.py can stop Freerouting routing signals through planes."""
import pcbnew

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage9_routed.kicad_pcb"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_planetype.kicad_pcb"
b = pcbnew.LoadBoard(SRC)

print("=== API surface ===")
print(" BOARD layer-type methods:", [s for s in dir(b) if "LayerType" in s])
print(" LT_ enums:", [s for s in dir(pcbnew) if s.startswith("LT_")])

print("=== current types ===")
for name, lid in (("F_Cu", pcbnew.F_Cu), ("In1_Cu", pcbnew.In1_Cu),
                  ("In2_Cu", pcbnew.In2_Cu), ("B_Cu", pcbnew.B_Cu)):
    try:
        print("  %-7s id=%-2d type=%s" % (name, lid, b.GetLayerType(lid)))
    except Exception as e:
        print("  %-7s GetLayerType failed: %r" % (name, e))

print("=== attempt to set In1/In2 to POWER type ===")
target = getattr(pcbnew, "LT_POWER", None)
print(" LT_POWER value:", target)
if target is not None and hasattr(b, "SetLayerType"):
    for lid in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        ok = b.SetLayerType(lid, target)
        print("  SetLayerType(%d, LT_POWER) ->" % lid, ok, "| now:", b.GetLayerType(lid))
    print(" save rc:", pcbnew.SaveBoard(OUT, b))
    b2 = pcbnew.LoadBoard(OUT)
    print(" after reload: In1=%s In2=%s" % (b2.GetLayerType(pcbnew.In1_Cu),
                                            b2.GetLayerType(pcbnew.In2_Cu)))
else:
    print(" LT_POWER or SetLayerType MISSING - plane declaration not available via Python")
