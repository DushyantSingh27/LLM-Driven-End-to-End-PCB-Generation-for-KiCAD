"""Probe: can a via sit AT a pad centre (via-in-pad), and does DRC accept it?
Decides whether 0.4mm-pitch WLCSP inner balls are reachable at all."""
import pcbnew

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage11_stitched.kicad_pcb"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_vip.kicad_pcb"
b = pcbnew.LoadBoard(SRC)

# H8 - the ball no through-via could reach
target = None
for fp in b.GetFootprints():
    if fp.GetReference() != "U1":
        continue
    for p in fp.Pads():
        if p.GetName() == "H8":
            target = p
print("H8 found:", target is not None,
      "| net:", target.GetNetname() if target else "-")
pos = target.GetPosition()
bb = target.GetBoundingBox()
print("pad size mm: %.3f x %.3f" % (pcbnew.ToMM(bb.GetWidth()),
                                    pcbnew.ToMM(bb.GetHeight())))

print("=== via-in-pad allowance settings present? ===")
ds = b.GetDesignSettings()
print(" ds attrs:", [s for s in dir(ds) if "ole" in s and "lear" in s.lower()][:6])
for n in ("m_HoleClearance", "m_HoleToHoleMin"):
    print("  %s: %s" % (n, hasattr(ds, n)))

print("=== place a 0.30/0.15 microvia AT the pad centre ===")
v = pcbnew.PCB_VIA(b)
v.SetPosition(pos)                       # exactly on the pad
v.SetDrill(pcbnew.FromMM(0.15))
v.SetWidth(pcbnew.FromMM(0.30))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(target.GetNet())
b.Add(v)
print(" placed; vias now:",
      sum(1 for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T))
# Re-pour: stale zones do not know about the new via, which produced false
# zone-clearance and hole-clearance violations on the first run.
from zones import pour_planes
for _n, _l, _a in pour_planes(b, (20.0, 20.0, 45.0, 45.0),
                              [(pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "/VDD_3V3")]):
    print("   re-poured", _n)
print(" save rc:", pcbnew.SaveBoard(OUT, b))

b2 = pcbnew.LoadBoard(OUT)
vs = [t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
at_pad = [t for t in vs
          if abs(t.GetPosition().x - pos.x) < 1000 and abs(t.GetPosition().y - pos.y) < 1000]
print(" after reload: total vias", len(vs), "| at H8 centre:", len(at_pad))
