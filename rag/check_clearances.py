import pcbnew
b = pcbnew.LoadBoard("C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\integrated_test.kicad_pcb")
ns = b.GetDesignSettings().m_NetSettings
for k in sorted(str(x) for x in ns.GetNetclasses().keys()):
    nc = ns.GetNetClassByName(k)
    print("  %-8s clearance=%.3f track=%.3f" %
          (k, pcbnew.ToMM(nc.GetClearance()), pcbnew.ToMM(nc.GetTrackWidth())))
