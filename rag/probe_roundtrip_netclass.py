"""Does a plain load->save preserve netclass clearances?
Isolates serialization from anything the stitching stage does."""
import pcbnew
O = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\"
SRC = O + "integrated_test.kicad_pcb"

def show(tag, path):
    b = pcbnew.LoadBoard(path)
    ns = b.GetDesignSettings().m_NetSettings
    vals = " ".join("%s=%.3f" % (k, pcbnew.ToMM(ns.GetNetClassByName(k).GetClearance()))
                    for k in sorted(str(x) for x in ns.GetNetclasses().keys()))
    pats = ns.GetNetclassPatternAssignments()
    print("%-14s %s" % (tag, vals))
    return b

b = show("loaded", SRC)
pcbnew.SaveBoard(O + "rt_plain.kicad_pcb", b)
show("plain save", O + "rt_plain.kicad_pcb")

# now with the pour step stage 11 performs
from zones import pour_planes
b2 = pcbnew.LoadBoard(SRC)
pour_planes(b2, (20.0, 20.0, 45.0, 45.0),
            [(pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "/VDD_3V3")])
pcbnew.SaveBoard(O + "rt_poured.kicad_pcb", b2)
show("after pour", O + "rt_poured.kicad_pcb")

print("=== what the FILE says (ground truth, not the API) ===")
import re
txt = open(O + "integrated_test.kicad_pcb", encoding="utf-8", errors="replace").read()
for m in re.finditer(r'\(net_class\s+"?(\w+)"?(.{0,200})', txt, re.S):
    cl = re.search(r'\(clearance\s+([\d.]+)\)', m.group(2))
    print("   %-8s clearance=%s" % (m.group(1), cl.group(1) if cl else "?"))
