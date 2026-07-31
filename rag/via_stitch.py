"""via_stitch.py - P7: connect plane-net pads to their planes with via + track.

WHY: Freerouting will not fan out into layers declared as planes (measured:
declaring In1/In2 as power removed all signal traces from them - the fix we
wanted - but also dropped all 39 GND/VDD_3V3 connections). Those are ours.

Geometry is MEASURED from the board (via_geom, pure + unit-tested). Pads that
cannot be escaped are REPORTED, never silently skipped - on fine-pitch parts
some inner balls are genuinely unreachable with through-vias.

Verified API: PCB_VIA(board), SetPosition/SetDrill/SetWidth/SetNet,
SetLayerPair(F_Cu,B_Cu), SetViaType(VIATYPE_THROUGH), board.Add.
NOTE: PCB_VIA.GetWidth() asserts in 9.0 without a layer arg - never call it.
PCB_TRACK is checked at runtime by assert_track_api() before use.
"""
import pcbnew
from via_geom import find_via_position

# Geometry knobs only. ELECTRICAL numbers come from the design-rules resolver
# per net class - hardcoding them here caused real DRC failures: a /VDD_3V3 via
# placed at the 0.09 fab floor while its POWER netclass requires 0.15.
STITCH_POLICY = {
    "hole_clearance_mm": 0.25,   # KiCad board-setup hole-to-copper default
    "max_reach_mm": 1.2,         # a long stub is not a fanout - give up instead
}


def assert_track_api():
    """PCB_TRACK authoring is the one call not yet probed - fail loudly, early."""
    missing = [m for m in ("SetStart", "SetEnd", "SetWidth", "SetLayer", "SetNet")
               if not hasattr(pcbnew.PCB_TRACK, m)]
    if missing:
        raise RuntimeError("PCB_TRACK missing: %s" % missing)
    return True


def _pad_radius_mm(pad):
    bb = pad.GetBoundingBox()
    return max(pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())) / 2.0


def collect_obstacles(board):
    """[(x, y, r, netname)] mm for every pad and existing via on the board."""
    obs = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pos = p.GetPosition()
            obs.append((pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y),
                        _pad_radius_mm(p), p.GetNetname()))
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            pos = t.GetPosition()
            # radius from drill + a nominal annulus (GetWidth() asserts in 9.0)
            obs.append((pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y),
                        pcbnew.ToMM(t.GetDrill()) / 2.0 + 0.125, t.GetNetname()))
    return obs


def stitch_planes(board, plane_nets, bounds_mm, net_rules, policy=STITCH_POLICY):
    """Place a via + connecting track for every pad on <plane_nets>.
    Returns (stitched, unstitched): lists of (ref, pad, netname[, xy])."""
    assert_track_api()
    obstacles = collect_obstacles(board)
    stitched, unstitched = [], []

    targets = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in plane_nets:
                targets.append((fp.GetReference(), p.GetName(), p))

    for ref, padname, pad in targets:
        net = pad.GetNet()
        netname = pad.GetNetname()
        pos = pad.GetPosition()
        pxy = (pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))
        prad = _pad_radius_mm(pad)
        rules = net_rules[netname]
        via_r = rules["via_dia_mm"] / 2.0
        hole_r = rules["via_drill_mm"] / 2.0
        others = [o for o in obstacles
                  if not (abs(o[0] - pxy[0]) < 1e-6 and abs(o[1] - pxy[1]) < 1e-6)]
        spot = find_via_position(pxy, prad, netname, others, via_r,
                                 rules["clearance_mm"], bounds_mm,
                                 track_w=rules["track_mm"], hole_r=hole_r,
                                 hole_clearance=policy["hole_clearance_mm"],
                                 max_mm=policy["max_reach_mm"])
        if spot is None:
            unstitched.append((ref, padname, netname))
            continue

        vx, vy = spot
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
        v.SetDrill(pcbnew.FromMM(rules["via_drill_mm"]))
        v.SetWidth(pcbnew.FromMM(rules["via_dia_mm"]))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net)
        board.Add(v)

        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pos)
        t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(vx), pcbnew.FromMM(vy)))
        t.SetWidth(pcbnew.FromMM(rules["track_mm"]))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(net)
        board.Add(t)

        obstacles.append((vx, vy, via_r, netname))
        stitched.append((ref, padname, netname, (vx, vy)))

    return stitched, unstitched
