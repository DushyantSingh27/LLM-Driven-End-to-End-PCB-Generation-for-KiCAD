"""Probe: is a courtyard cache-rebuild exposed? If yes, verify it fixes the
in-memory board; report which fix layout_pipeline should use."""
import pcbnew
from board_builder import place_all_grid

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"
TMP = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_tmp2.kicad_pcb"

print("=== candidate cache methods ===")
fp_methods = [s for s in dir(pcbnew.FOOTPRINT) if "ourtyard" in s or "ache" in s]
bd_methods = [s for s in dir(pcbnew.BOARD) if "ourtyard" in s or "ache" in s]
print("FOOTPRINT:", fp_methods)
print("BOARD:", bd_methods)

board, comps = place_all_grid(NET, TMP)
fp = [f for f in board.GetFootprints() if f.GetReference() == "C1"][0]

def cy_wh(f):
    bb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return (round(pcbnew.ToMM(bb.GetWidth()), 2), round(pcbnew.ToMM(bb.GetHeight()), 2))

print("before:", cy_wh(fp))
if hasattr(fp, "BuildCourtyardCaches"):
    fp.BuildCourtyardCaches()
    print("after fp.BuildCourtyardCaches():", cy_wh(fp))
    ok = cy_wh(fp) == (3.49, 2.05)
    print("VERDICT:", "USE BuildCourtyardCaches" if ok else "method exists but didn't fix -> use save-reload")
else:
    print("VERDICT: no rebuild method on FOOTPRINT -> use save-reload seam")
