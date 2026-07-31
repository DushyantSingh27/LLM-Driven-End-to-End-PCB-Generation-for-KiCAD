"""Verify the integrated board: layer types, netclasses, zones, placement."""
import pcbnew
B = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\integrated_test.kicad_pcb"
b = pcbnew.LoadBoard(B)
ns = b.GetDesignSettings().m_NetSettings

lt = [b.GetLayerType(l) for l in (pcbnew.In1_Cu, pcbnew.In2_Cu)]
print("layer types In1/In2:", lt, "(1=POWER)  ->", "OK" if lt == [1, 1] else "STALE")

print("footprints:", len(b.GetFootprints()),
      "| pads:", sum(f.GetPadCount() for f in b.GetFootprints()))

zs = list(b.Zones())
print("zones:", len(zs))
for z in zs:
    print("   net=%-10s layer=%d filled=%s" % (z.GetNetname(), z.GetLayer(), z.IsFilled()))

print("netclasses:", sorted(str(k) for k in ns.GetNetclasses().keys()))
for n in ("/VDD_3V3", "GND", "/VREF_PLUS", "/SPI_SCK"):
    net = b.FindNet(n)
    print("   %-12s class=%s" % (n, net.GetNetClassName() if net else "MISSING"))

ok = (lt == [1, 1] and len(zs) == 2 and all(z.IsFilled() for z in zs)
      and len(b.GetFootprints()) == 22)
print("INTEGRATED BOARD", "PASS" if ok else "FAIL")
