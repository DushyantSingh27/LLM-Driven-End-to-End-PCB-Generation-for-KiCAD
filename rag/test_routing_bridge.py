"""Exercise the routing bridge standalone before wiring it into the pipeline."""
import pcbnew, os
from routing import (find_java, find_jar, export_dsn, run_freerouting,
                     import_ses, parse_router_log)
from design_rules import router_clearance_mm
from board_builder import save_board

O = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\"
SRC = O + "stage11_stitched.kicad_pcb"

print("java:", find_java())
print("jar :", find_jar())

rc = router_clearance_mm(0.09, 0.25, 0.20, 0.45)
print("derived router clearance: %.4f mm" % rc)

b = pcbnew.LoadBoard(SRC)
export_dsn(b, O + "bridge_test.dsn", router_clearance_mm=rc,
           scratch_path=O + "bridge_scratch.kicad_pcb")
print("dsn written:", os.path.exists(O + "bridge_test.dsn"))

ok, stats, log = run_freerouting(O + "bridge_test.dsn", O + "bridge_test.ses",
                                 exclude_nets=("GND",))
print("router ok:", ok)
for k in ("returncode", "started_unrouted", "final_unrouted", "passes", "saved"):
    print("   %-18s %s" % (k, stats.get(k)))
print("   unrouted nets:", stats.get("unrouted_nets"))

if ok:
    t, v = import_ses(b, O + "bridge_test.ses")
    print("after import -> traces:", t, "vias:", v)
    print("save:", save_board(b, O + "bridge_test.kicad_pcb"))
