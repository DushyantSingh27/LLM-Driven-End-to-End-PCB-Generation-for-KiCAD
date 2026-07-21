"""Stage-6 runner: constructive placement + metrics + save/reload verify."""
import pcbnew, itertools
from board_builder import save_board
from netlist_reader import parse_netlist_nets
from grouping import parse_netlist_values, assign_decaps
from placement_engine import place_all, POLICY

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4_setup.kicad_pcb"
NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage6_placed.kicad_pcb"

print("SetOrientationDegrees available:",
      hasattr(pcbnew.FOOTPRINT, "SetOrientationDegrees"))   # probe only

board = pcbnew.LoadBoard(SRC)
nets = parse_netlist_nets(NET)
asg = assign_decaps(nets, parse_netlist_values(NET))
moves = place_all(board, asg)
assert save_board(board, OUT)
print("moved:", len(moves), "parts")

b2 = pcbnew.LoadBoard(OUT)
x0, y0, x1, y1 = POLICY["board"]
boxes, outside = {}, []
for fp in b2.GetFootprints():
    bb = fp.GetBoundingBox(False)
    l, t = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    r, b_ = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
    boxes[fp.GetReference()] = (l, t, r, b_)
    if l < x0 or t < y0 or r > x1 or b_ > y1:
        outside.append(fp.GetReference())

overlaps = []
for a, b in itertools.combinations(sorted(boxes), 2):
    la, ta, ra, ba = boxes[a]; lb, tb, rb, bb_ = boxes[b]
    if la < rb and lb < ra and ta < bb_ and tb < ba:
        overlaps.append((a, b))

# decap metric: pad-center to cap-center distance per pair
import math
pos = {fp.GetReference(): fp for fp in b2.GetFootprints()}
worst = (0.0, None)
for rail, a in asg.items():
    for (ic, pin), cap in a["pairs"]:
        if cap is None: continue
        icfp = pos[ic]
        pads = [p for p in icfp.Pads() if p.GetName() == pin]
        pp, cp = pads[0].GetPosition(), pos[cap].GetPosition()
        d = math.hypot(pcbnew.ToMM(pp.x-cp.x), pcbnew.ToMM(pp.y-cp.y))
        if d > worst[0]: worst = (round(d,2), (rail, ic, pin, cap))
print("outside outline:", outside)
print("bbox overlaps:", len(overlaps), overlaps[:8])
print("worst decap distance (mm):", worst)
print("STAGE6 SELFCHECK", "PASS" if (not outside) else "FAIL")
