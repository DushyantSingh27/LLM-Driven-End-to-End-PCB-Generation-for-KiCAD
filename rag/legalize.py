"""legalize.py - P5: courtyard-overlap resolution, force-directed (v2).
v1 (sequential pairwise shoves) oscillated 8,6,8,6...: fixes fought each
other. v2 accumulates ALL separation vectors per part per iteration, applies
once, damped 0.6 - simultaneous update, no intra-iteration thrash.
Anchors (U1, U2) never move. Bounded; loud failure carries history."""
import pcbnew

CLEAR_MM = 0.10
EPS_MM = 0.02     # sub-epsilon intrusions into the clearance buffer = converged
MAX_ITER = 60
DAMP = 0.6


def courtyard_rect(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
            pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))


def legalize(board, fixed=("U1", "U2"), clear_mm=CLEAR_MM):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    moved_total = {}
    history = []
    collisions = []
    for it in range(MAX_ITER):
        rects = {r: courtyard_rect(f) for r, f in fps.items()}
        refs = sorted(rects)
        collisions = []
        for i, a in enumerate(refs):
            for b in refs[i+1:]:
                la, ta, ra, ba = rects[a]; lb, tb, rb, bb_ = rects[b]
                ox = min(ra, rb) - max(la, lb) + clear_mm
                oy = min(ba, bb_) - max(ta, tb) + clear_mm
                if ox > EPS_MM and oy > EPS_MM:
                    collisions.append((a, b, ox, oy))
        history.append(len(collisions))
        if not collisions:
            return it, moved_total
        pair_ids = {(a, b) for a, b, _, _ in collisions}
        stale = pair_ids & getattr(legalize, "_prev", set())
        legalize._prev = pair_ids
        force = {}
        for a, b, ox, oy in collisions:
            la, ta, ra, ba = rects[a]; lb, tb, rb, bb_ = rects[b]
            prefer_x = (ox <= oy)
            if (a, b) in stale and it % 2 == 1:
                prefer_x = not prefer_x   # escape: flip axis for persistent pairs
            if prefer_x:
                d = ox
                sign_b = 1 if (lb + rb) >= (la + ra) else -1
                va = (-sign_b * d, 0.0); vb = (sign_b * d, 0.0)
            else:
                d = oy
                sign_b = 1 if (tb + bb_) >= (ta + ba) else -1
                va = (0.0, -sign_b * d); vb = (0.0, sign_b * d)
            for ref, v in ((a, va), (b, vb)):
                if ref in fixed:
                    continue
                fx, fy = force.get(ref, (0.0, 0.0))
                force[ref] = (fx + v[0], fy + v[1])
        if not force:
            raise RuntimeError("only fixed parts overlap: %s" % collisions)
        for ref, (fx, fy) in force.items():
            f = fps[ref]; p = f.GetPosition()
            f.SetPosition(pcbnew.VECTOR2I(
                p.x + pcbnew.FromMM(fx * DAMP),
                p.y + pcbnew.FromMM(fy * DAMP)))
            moved_total[ref] = moved_total.get(ref, 0.0) \
                + abs(fx * DAMP) + abs(fy * DAMP)
    raise RuntimeError(
        "legalize: unresolved after %d iterations\n"
        "collision counts per iteration: %s\n"
        "final stuck pairs: %s"
        % (MAX_ITER, history,
           [(a, b, round(ox, 2), round(oy, 2))
            for a, b, ox, oy in collisions]))
