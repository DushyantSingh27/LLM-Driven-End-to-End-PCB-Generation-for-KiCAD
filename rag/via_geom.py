"""via_geom.py - PURE geometry for via stitching (no pcbnew, unit-testable).

A via alone connects nothing: the pad needs a TRACK to the via. So a candidate
position is legal only if BOTH (a) the via clears every other-net obstacle and
(b) the straight pad->via segment clears them too, by clearance + track/2.
This is what makes interior fine-pitch balls genuinely unreachable rather than
apparently-solvable by placing a via further away.

Clearance rule: different-net obstacles need full clearance; same-net obstacles
need only non-overlap (same-net copper may touch; via-in-pad is a separate
process we do not assume).
"""
import math


def _seg_point_dist(ax, ay, bx, by, px, py):
    """Shortest distance from point P to segment AB."""
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 <= 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _clear(obstacles, net, need_fn, check_fn):
    for (ox, oy, orad, onet) in obstacles:
        if check_fn(ox, oy) < need_fn(orad, onet) - 1e-9:
            return False
    return True


def find_via_position(pad_xy, pad_r, pad_net, obstacles, via_r, clearance,
                      bounds, track_w=0.15, hole_r=0.10, hole_clearance=0.25,
                      start_mm=0.35, max_mm=1.2, step_mm=0.05, n_angles=32):
    """Legal via centre near a pad, whose pad->via track is also legal.
    TWO clearance families must hold against different-net copper:
      copper: via_r + obs_r + clearance
      hole:   hole_r + obs_r + hole_clearance   (KiCad board-setup rule)
    Measured failure when hole clearance was ignored: 0.2437 < 0.25.
    Same-net copper may touch (exempt from track check); via never on the pad.
    obstacles: [(x,y,r,netname)] EXCLUDING the source pad. Returns (x,y)|None."""
    px, py = pad_xy
    x0, y0, x1, y1 = bounds
    r = max(start_mm, via_r + pad_r)
    while r <= max_mm + 1e-9:
        for i in range(n_angles):
            a = 2.0 * math.pi * i / n_angles
            cx, cy = px + r * math.cos(a), py + r * math.sin(a)
            if not (x0 + via_r <= cx <= x1 - via_r and y0 + via_r <= cy <= y1 - via_r):
                continue
            ok = True
            for (ox, oy, orad, onet) in obstacles:
                same = (onet == pad_net)
                d = math.hypot(cx - ox, cy - oy)
                need_cu = via_r + orad + (0.0 if same else clearance)
                need_hole = 0.0 if same else (hole_r + orad + hole_clearance)
                if d < max(need_cu, need_hole) - 1e-9:
                    ok = False
                    break
                if not same:
                    need_t = track_w / 2.0 + orad + clearance
                    if _seg_point_dist(px, py, cx, cy, ox, oy) < need_t - 1e-9:
                        ok = False
                        break
            if ok:
                return (round(cx, 4), round(cy, 4))
        r += step_mm
    return None
