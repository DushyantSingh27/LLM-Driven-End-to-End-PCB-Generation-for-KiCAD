"""Measure the real cost of clearance inflation: routability vs hole violations."""
import pcbnew, os, subprocess
from routing import export_dsn, run_freerouting, import_ses
from board_builder import save_board

O = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\"
SRC = O + "stage11_stitched.kicad_pcb"
KCLI = "C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe"

def drc_counts(pcb, rpt):
    subprocess.run([KCLI, "pcb", "drc", "--output", rpt, pcb],
                   capture_output=True, text=True)
    txt = open(rpt, encoding="utf-8", errors="replace").read()
    import re, collections
    return collections.Counter(re.findall(r'^\[([a-z_]+)\]', txt, re.M))

for tag, clr in (("none", None), ("0.125", 0.125)):
    dsn = O + "exp_%s.dsn" % tag
    ses = O + "exp_%s.ses" % tag
    pcb = O + "exp_%s.kicad_pcb" % tag
    b = pcbnew.LoadBoard(SRC)
    export_dsn(b, dsn, router_clearance_mm=clr,
               scratch_path=(O + "exp_scratch.kicad_pcb") if clr else None)
    ok, stats, log = run_freerouting(dsn, ses, exclude_nets=("GND",))
    if not ok:
        print(tag, "ROUTER FAILED", stats); continue
    import_ses(b, ses)
    # re-pour: zones must know about the routed copper, or DRC reports
    # violations against stale fill
    from zones import pour_planes
    pour_planes(b, (20.0, 20.0, 45.0, 45.0),
                [(pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "/VDD_3V3")])
    save_board(b, pcb)
    c = drc_counts(pcb, O + "exp_%s.rpt" % tag)
    print("clearance=%-6s unrouted=%-3s | DRC: unconn=%-3d hole=%-3d clear=%-3d"
          % (tag, stats["final_unrouted"], c["unconnected_items"],
             c["hole_clearance"], c["clearance"]))
