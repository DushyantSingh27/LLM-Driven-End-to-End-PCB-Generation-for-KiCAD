"""geometry.py - P1: geometric facts for placement (courtyards, power-pad map).
All outputs in mm, positions relative to footprint center. Edge classification:
dominant offset axis decides left/right vs top/bottom; ties (corners) -> y-edge."""
import pcbnew


def footprint_size_mm(fp):
    """(w, h) of the footprint bbox in mm (conservative: includes text)."""
    bb = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()))


def classify_edge(dx, dy):
    """Which side of the IC a pad sits on. dy negative = top (KiCad +y is down)."""
    if abs(dx) > abs(dy):
        return "left" if dx < 0 else "right"
    return "top" if dy < 0 else "bottom"


def power_pad_map(board, ref, rail_filter=None):
    """[(pad_name, netname, dx_mm, dy_mm, edge)] for pads on power rails of <ref>.
    rail_filter: callable(netname)->bool; default: /V* or VDDA."""
    if rail_filter is None:
        rail_filter = lambda n: n.startswith("/V") or n == "VDDA"
    out = []
    for fp in board.GetFootprints():
        if fp.GetReference() != ref:
            continue
        c = fp.GetPosition()
        for p in fp.Pads():
            nn = p.GetNetname()
            if rail_filter(nn):
                dx = pcbnew.ToMM(p.GetPosition().x - c.x)
                dy = pcbnew.ToMM(p.GetPosition().y - c.y)
                out.append((p.GetName(), nn, round(dx, 3), round(dy, 3),
                            classify_edge(dx, dy)))
    return out
