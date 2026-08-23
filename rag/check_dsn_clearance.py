import pcbnew, re
from routing import export_dsn
from design_rules import router_clearance_mm
O = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\"
b = pcbnew.LoadBoard(O + "stage11_stitched.kicad_pcb")
ns = b.GetDesignSettings().m_NetSettings
before = pcbnew.ToMM(ns.GetEffectiveNetClass("/VDD_3V3").GetClearance())
export_dsn(b, O + "chk.dsn", router_clearance_mm=router_clearance_mm(0.09, 0.25, 0.20, 0.45))
after = pcbnew.ToMM(ns.GetEffectiveNetClass("/VDD_3V3").GetClearance())
print("board clearance before=%.3f after=%.3f (must match)" % (before, after))
vals = re.findall(r'\(clearance (\d+(?:\.\d+)?)\)', open(O + "chk.dsn").read())
import collections; print("DSN clearance values:", collections.Counter(vals))
