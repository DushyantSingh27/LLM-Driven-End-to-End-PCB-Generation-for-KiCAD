"""Stage-7 runner: legalize stage-6 placement, re-verify, save."""
import pcbnew, itertools, math
from board_builder import save_board
from netlist_reader import parse_netlist_nets
from grouping import parse_netlist_values, assign_decaps
from legalize import legalize, courtyard_rect
from placement_engine import POLICY

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage6_placed.kicad_pcb"
NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage7_legal.kicad_pcb"

board = pcbnew.LoadBoard(SRC)
iters, moved = legalize(board)
print("converged in", iters, "iterations | parts nudged:",
      {k: round(v,2) for k, v in sorted(moved.items())})
assert save_board(board, OUT)

b2 = pcbnew.LoadBoard(OUT)
rects = {f.GetReference(): courtyard_rect(f) for f in b2.GetFootprints()}
x0, y0, x1, y1 = POLICY["board"]
outside = [r for r, (l, t, rr, bb) in rects.items()
           if l < x0 or t < y0 or rr > x1 or bb > y1]
overlaps = []
for a, b in itertools.combinations(sorted(rects), 2):
    la, ta, ra, ba = rects[a]; lb, tb, rb, bb_ = rects[b]
    if la < rb and lb < ra and ta < bb_ and tb < ba:
        overlaps.append((a, b))

asg = assign_decaps(parse_netlist_nets(NET), parse_netlist_values(NET))
pos = {f.GetReference(): f for f in b2.GetFootprints()}
worst = (0.0, None)
for rail, a in asg.items():
    for (ic, pin), cap in a["pairs"]:
        if cap is None: continue
        pads = [p for p in pos[ic].Pads() if p.GetName() == pin]
        pp, cp = pads[0].GetPosition(), pos[cap].GetPosition()
        d = math.hypot(pcbnew.ToMM(pp.x-cp.x), pcbnew.ToMM(pp.y-cp.y))
        if d > worst[0]: worst = (round(d,2), (rail, ic, pin, cap))
print("outside outline:", outside)
print("courtyard overlaps:", overlaps)
print("worst decap distance (mm):", worst)
print("STAGE7 SELFCHECK", "PASS" if (not outside and not overlaps) else "FAIL")
