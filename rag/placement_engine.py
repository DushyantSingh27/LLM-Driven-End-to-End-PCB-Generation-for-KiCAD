"""placement_engine.py - P4: constructive placement (stage A).
Rules: U1 center-anchored; paired decaps in per-edge lanes outside a fanout
annulus (ST item 19 + WLCSP escape reserve); U2 + caps in analog zone right
(VREF+/VDDA balls on U1 right edge); bulk caps clustered; pull-ups between
endpoints. All geometry in mm; KiCad +y is DOWN."""
import pcbnew
from geometry import power_pad_map, footprint_size_mm, classify_edge

POLICY = {
    "annulus_mm": 2.0,        # fanout reserve around U1 courtyard
    "lane_gap_mm": 0.4,       # gap between caps in a lane
    "board": (20.0, 20.0, 45.0, 45.0),   # x0,y0,x1,y1 of outline
}


def _fp(board, ref):
    for f in board.GetFootprints():
        if f.GetReference() == ref:
            return f
    raise RuntimeError("no footprint " + ref)


def _move(board, ref, x, y):
    _fp(board, ref).SetPosition(
        pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))


def place_all(board, assignment):
    """Stage-A constructive pass. Returns {ref: (x, y)} of every move."""
    x0, y0, x1, y1 = POLICY["board"]
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    moves = {}

    u1 = _fp(board, "U1")
    _move(board, "U1", cx, cy); moves["U1"] = (cx, cy)
    u1w, u1h = footprint_size_mm(u1)

    # ball -> (edge, lateral coordinate) from P1, AFTER the move
    pmap = {name: (edge, dx, dy)
            for name, net, dx, dy, edge in power_pad_map(board, "U1")}

    # collect paired decaps per edge: (lateral_sort_key, cap_ref)
    lanes = {"top": [], "bottom": [], "left": [], "right": []}
    u2_caps = []
    for rail, a in assignment.items():
        for (ic, pin), cap in a["pairs"]:
            if cap is None:
                continue
            if ic == "U2":
                u2_caps.append(cap)
                continue
            edge, dx, dy = pmap[pin]
            lanes[edge].append((dx if edge in ("top", "bottom") else dy, cap))

    claimed = set(["U1", "U2", "R1", "R2", "R3", "R4"]) | set(u2_caps)
    for a in assignment.values():
        claimed |= {c for _, c in a["pairs"] if c}
        claimed |= set(a["bulk"])
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in claimed:
            continue
        sig = {p.GetNetname() for p in fp.Pads()} - {"GND", ""}
        anchor = None
        for p in u1.Pads():
            if p.GetNetname() in sig:
                anchor = p
                break
        if anchor is None:
            raise RuntimeError("orphan %s shares no net with U1" % ref)
        adx = pcbnew.ToMM(anchor.GetPosition().x - u1.GetPosition().x)
        ady = pcbnew.ToMM(anchor.GetPosition().y - u1.GetPosition().y)
        e = classify_edge(adx, ady)
        lanes[e].append((adx if e in ("top", "bottom") else ady, ref))

    cap_w, cap_h = footprint_size_mm(_fp(board, lanes["top"][0][1])) \
        if lanes["top"] else (3.45, 2.01)
    ann = POLICY["annulus_mm"]; gap = POLICY["lane_gap_mm"]

    def lay_lane(edge, items):
        items.sort()
        n = len(items)
        if not n:
            return
        if edge in ("top", "bottom"):
            pitch = cap_w + gap
            ylane = cy - (u1h/2 + ann + cap_h/2) if edge == "top" \
                else cy + (u1h/2 + ann + cap_h/2)
            start = cx - pitch * (n - 1) / 2.0
            for i, (_, cap) in enumerate(items):
                _move(board, cap, start + i*pitch, ylane)
                moves[cap] = (start + i*pitch, ylane)
        else:
            pitch = cap_h + gap
            xlane = cx - (u1w/2 + ann + cap_w/2) if edge == "left" \
                else cx + (u1w/2 + ann + cap_w/2)
            start = cy - pitch * (n - 1) / 2.0
            for i, (_, cap) in enumerate(items):
                _move(board, cap, xlane, start + i*pitch)
                moves[cap] = (xlane, start + i*pitch)

    for edge, items in lanes.items():
        lay_lane(edge, items)

    # analog zone: U2 lower-right, its decaps stacked to its left
    u2x, u2y = x1 - 4.5, y1 - 5.0
    _move(board, "U2", u2x, u2y); moves["U2"] = (u2x, u2y)
    for i, cap in enumerate(sorted(u2_caps)):
        p = (u2x - 4.2, u2y + i * (cap_h + gap))
        _move(board, cap, *p); moves[cap] = p

    # bulk caps: supply cluster bottom-left
    bulk = sorted(c for a in assignment.values() for c in a["bulk"])
    for i, cap in enumerate(bulk):
        p = (x0 + 4.0 + i * (cap_w + gap), y1 - 3.0)
        _move(board, cap, *p); moves[cap] = p

    # pull-ups: column between U1 and U2 zones
    for i, r in enumerate(["R1", "R2", "R3", "R4"]):
        p = (x0 + 4.0 + i * (cap_w + gap), y0 + 3.0)
        _move(board, r, *p); moves[r] = p
    return moves
