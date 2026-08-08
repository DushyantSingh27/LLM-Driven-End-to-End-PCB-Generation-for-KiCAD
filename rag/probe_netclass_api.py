"""Probe: how to CREATE a netclass, set widths, and assign nets (pcbnew 9.0)."""
import pcbnew
B = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage9_routed.kicad_pcb"
b = pcbnew.LoadBoard(B)
ns = b.GetDesignSettings().m_NetSettings

print("=== NETCLASS constructor + setters ===")
try:
    nc = pcbnew.NETCLASS("PWR")
    print(" NETCLASS('PWR') OK, name:", nc.GetName())
except Exception as e:
    print(" NETCLASS(name) failed:", repr(e))
    nc = None
if nc:
    for m in ("SetTrackWidth","SetClearance","SetViaDiameter","SetViaDrill",
              "SetuViaDiameter","SetDiffPairWidth","SetName","GetTrackWidth"):
        print("   %-18s %s" % (m, hasattr(nc, m)))

print("=== NET_SETTINGS containers ===")
ncs = ns.GetNetclasses()
print(" GetNetclasses type:", type(ncs).__name__, "| count:", len(ncs))
print(" keys:", list(ncs.keys())[:5] if hasattr(ncs, "keys") else "n/a")
print(" NET_SETTINGS methods:", [s for s in dir(ns) if "etclass" in s or "Netclass" in s])

print("=== assignment mechanisms ===")
print(" pattern assignments:", type(ns.GetNetclassPatternAssignments()).__name__)
net = b.FindNet("GND")
print(" NETINFO_ITEM methods:", [s for s in dir(net) if "lass" in s.lower()])
print(" default netclass track width (mm):",
      pcbnew.ToMM(ns.GetDefaultNetclass().GetTrackWidth()))
