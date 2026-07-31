"""Probe: how to INSERT a netclass and ASSIGN nets to it (pcbnew 9.0).
Tries each candidate mechanism independently; reports which work and whether
the result survives save->reload. No guessing carried into rules_apply.py."""
import pcbnew

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage9_routed.kicad_pcb"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_netclass.kicad_pcb"
b = pcbnew.LoadBoard(SRC)
ns = b.GetDesignSettings().m_NetSettings

nc = pcbnew.NETCLASS("PWR")
nc.SetTrackWidth(pcbnew.FromMM(0.25))
nc.SetClearance(pcbnew.FromMM(0.15))
nc.SetViaDiameter(pcbnew.FromMM(0.45))
nc.SetViaDrill(pcbnew.FromMM(0.20))
print("built NETCLASS PWR, track =", pcbnew.ToMM(nc.GetTrackWidth()), "mm")

print("=== INSERTION candidates ===")
def count():
    try: return len(ns.GetNetclasses())
    except Exception as e: return "err:%r" % e

print(" before:", count())
try:
    ns.GetNetclasses()["PWR"] = nc
    print(" (a) map['PWR']=nc      -> count now", count())
except Exception as e:
    print(" (a) map assignment failed:", repr(e))
try:
    ns.SetNetclass("PWR", nc)
    print(" (b) SetNetclass(name,nc) -> count now", count())
except Exception as e:
    print(" (b) SetNetclass failed:", repr(e))
try:
    print(" HasNetclass('PWR'):", ns.HasNetclass("PWR"))
except Exception as e:
    print(" HasNetclass failed:", repr(e))

print("=== ASSIGNMENT candidates for /VDD_3V3 ===")
net = b.FindNet("/VDD_3V3")
print(" current class name:", net.GetNetClassName())
try:
    ns.SetNetclassPatternAssignment("/VDD_3V3", "PWR")
    print(" (c) SetNetclassPatternAssignment OK")
except Exception as e:
    print(" (c) pattern assignment failed:", repr(e))
try:
    net.SetNetClass(nc)
    print(" (d) net.SetNetClass(nc) OK -> now:", net.GetNetClassName())
except Exception as e:
    print(" (d) net.SetNetClass failed:", repr(e))
try:
    ns.RecomputeEffectiveNetclasses()
    print(" RecomputeEffectiveNetclasses OK -> class name:", net.GetNetClassName())
except Exception as e:
    print(" Recompute failed:", repr(e))

print("=== persistence ===")
print(" save rc:", pcbnew.SaveBoard(OUT, b))
b2 = pcbnew.LoadBoard(OUT)
ns2 = b2.GetDesignSettings().m_NetSettings
try:
    print(" classes after reload:", list(ns2.GetNetclasses().keys()))
except Exception as e:
    print(" listing failed:", repr(e))
n2 = b2.FindNet("/VDD_3V3")
print(" /VDD_3V3 class after reload:", n2.GetNetClassName())
try:
    eff = ns2.GetEffectiveNetClass("/VDD_3V3")
    print(" effective track width (mm):", pcbnew.ToMM(eff.GetTrackWidth()))
except Exception as e:
    print(" effective class lookup failed:", repr(e))
