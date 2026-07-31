import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
print("layer types:", [b.GetLayerType(l) for l in (pcbnew.In1_Cu, pcbnew.In2_Cu)])
print("export rc:", pcbnew.ExportSpecctraDSN(b, sys.argv[2]))
