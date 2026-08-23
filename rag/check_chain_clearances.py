"""Where does 0.15 survive? Walk the chain of boards the experiment uses."""
import pcbnew
O = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\"
for name in ("integrated_test.kicad_pcb", "stage11_stitched.kicad_pcb",
             "exp_scratch.kicad_pcb"):
    try:
        b = pcbnew.LoadBoard(O + name)
    except Exception as e:
        print(name, "-> load failed:", e); continue
    ns = b.GetDesignSettings().m_NetSettings
    vals = []
    for k in sorted(str(x) for x in ns.GetNetclasses().keys()):
        nc = ns.GetNetClassByName(k)
        vals.append("%s=%.3f" % (k, pcbnew.ToMM(nc.GetClearance())))
    # effective class for a POWER net is what actually governs
    try:
        eff = pcbnew.ToMM(ns.GetEffectiveNetClass("/VDD_3V3").GetClearance())
    except Exception as e:
        eff = "err %r" % e
    print("%-32s %s | effective(/VDD_3V3)=%s" % (name, " ".join(vals), eff))
