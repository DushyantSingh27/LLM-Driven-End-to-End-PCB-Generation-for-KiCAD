"""Probe: import the routed .ses back into the board and verify tracks/vias appear."""
import pcbnew, inspect

PCB = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage8_pours.kicad_pcb"
SES = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage8_pours.ses"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage9_routed.kicad_pcb"

print("signature:", pcbnew.ImportSpecctraSES.__doc__)
b = pcbnew.LoadBoard(PCB)
print("before -> tracks:", len(list(b.GetTracks())))
try:
    rc = pcbnew.ImportSpecctraSES(b, SES)
except TypeError as e:
    print("(board, path) failed:", e)
    rc = pcbnew.ImportSpecctraSES(SES)
print("import rc:", rc)

tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
print("after -> traces:", len(tracks), "| vias:", len(vias))
print("save rc:", pcbnew.SaveBoard(OUT, b))

b2 = pcbnew.LoadBoard(OUT)
t2 = [t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
v2 = [t for t in b2.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
print("after reload -> traces:", len(t2), "| vias:", len(v2))
print("SES-IMPORT SELFCHECK", "PASS" if (len(t2) > 0 and len(v2) > 0) else "FAIL")
