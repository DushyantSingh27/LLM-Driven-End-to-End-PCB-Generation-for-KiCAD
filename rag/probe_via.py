"""Probe: PCB_VIA authoring API in pcbnew 9.0 - construct, place, net, layers,
persistence. Nothing here is assumed; via_stitch.py will use only what passes."""
import pcbnew

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\integrated_test.kicad_pcb"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_via.kicad_pcb"
b = pcbnew.LoadBoard(SRC)

print("=== via symbols in module ===")
print(" classes:", [s for s in dir(pcbnew) if "VIA" in s.upper() and "VIATYPE" not in s.upper()][:10])
print(" VIATYPE enums:", [s for s in dir(pcbnew) if "VIATYPE" in s.upper()])

print("=== construct ===")
try:
    v = pcbnew.PCB_VIA(b)
    print(" PCB_VIA(board) OK")
except Exception as e:
    print(" PCB_VIA(board) FAILED:", repr(e)); raise SystemExit

print("=== method presence ===")
for m in ("SetPosition","SetDrill","SetWidth","SetNet","SetNetCode","SetLayerPair",
          "SetViaType","SetTopLayer","SetBottomLayer","GetDrill","GetWidth"):
    print("   %-16s %s" % (m, hasattr(v, m)))

print("=== find a GND pad to stitch beside ===")
gnd = b.FindNet("GND")
print(" GND net found:", gnd is not None, "| netcode:", gnd.GetNetCode() if gnd else "-")
target = None
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == "GND":
            target = (fp.GetReference(), p.GetName(), p.GetPosition())
            break
    if target: break
print(" target pad:", target[0], target[1],
      round(pcbnew.ToMM(target[2].x),3), round(pcbnew.ToMM(target[2].y),3))

print("=== build one via 0.6mm to the right of that pad ===")
pos = pcbnew.VECTOR2I(target[2].x + pcbnew.FromMM(0.6), target[2].y)
v.SetPosition(pos)
v.SetDrill(pcbnew.FromMM(0.20))
v.SetWidth(pcbnew.FromMM(0.45))
v.SetNet(gnd)
try:
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    print(" SetLayerPair(F_Cu, B_Cu) OK")
except Exception as e:
    print(" SetLayerPair failed:", repr(e))
try:
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    print(" SetViaType(THROUGH) OK")
except Exception as e:
    print(" SetViaType failed:", repr(e))
b.Add(v)
print(" vias on board now:", sum(1 for t in b.GetTracks() if t.Type()==pcbnew.PCB_VIA_T))

print("=== persistence ===")
print(" save rc:", pcbnew.SaveBoard(OUT, b))
b2 = pcbnew.LoadBoard(OUT)
vs = [t for t in b2.GetTracks() if t.Type()==pcbnew.PCB_VIA_T]
print(" vias after reload:", len(vs))
if vs:
    v2 = vs[0]
    print("  net:", v2.GetNetname(),
          "| drill mm:", round(pcbnew.ToMM(v2.GetDrill()),3),
          "| width mm:", round(pcbnew.ToMM(v2.GetWidth()),3))
print("PROBE COMPLETE")
