"""zones.py - P6: copper plane pours (ST item 12: GND and VDD planes).
Verified 9.0 surface: ZONE(board), SetLayer, SetNet, Outline()+NewOutline/Append,
SetPadConnection(ZONE_CONNECTION_THERMAL), SetThermalReliefGap/SpokeWidth,
SetFillMode(ZONE_FILL_MODE_POLYGONS), SetAssignedPriority (NOT SetPriority),
SetMinThickness, ZONE_FILLER. Layer ids: In1=4, In2=6.
Numbers: PCB Power DFM (thermal 0.25/0.20, sliver 0.20). Edge pullback 0.3mm
is a PLACEHOLDER - PCB Power states 'keep copper from edge' without a value."""
import pcbnew

PLANE_POLICY = {
    "thermal_gap_mm": 0.25,      # PCB Power spec
    "thermal_spoke_mm": 0.20,    # PCB Power spec
    "min_thickness_mm": 0.20,    # PCB Power copper-sliver floor
    "edge_pullback_mm": 0.30,    # PLACEHOLDER - unsourced, confirm with fab
}

# layer id -> net name; ids verified by probe
PLANES = [(pcbnew.In1_Cu, "GND"), (pcbnew.In2_Cu, "/VDD_3V3")]


def add_plane(board, layer_id, netname, outline_mm, policy=PLANE_POLICY, priority=0):
    """Pour a rectangular plane on <layer_id> for <netname>.
    outline_mm: (x0, y0, x1, y1) board outline; zone is inset by edge_pullback."""
    net = board.FindNet(netname)
    if net is None:
        raise RuntimeError("no net named %r on board" % netname)
    pb = policy["edge_pullback_mm"]
    x0, y0, x1, y1 = outline_mm
    x0 += pb; y0 += pb; x1 -= pb; y1 -= pb

    z = pcbnew.ZONE(board)
    z.SetLayer(layer_id)
    z.SetNet(net)
    z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)     # not hatch (PCB Power 3A)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(pcbnew.FromMM(policy["thermal_gap_mm"]))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(policy["thermal_spoke_mm"]))
    z.SetMinThickness(pcbnew.FromMM(policy["min_thickness_mm"]))
    z.SetAssignedPriority(priority)

    o = z.Outline()
    o.NewOutline()
    for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(pcbnew.FromMM(px), pcbnew.FromMM(py))
    board.Add(z)
    return z


def pour_planes(board, outline_mm, planes=PLANES):
    """Add all planes, then run the filler. Returns [(netname, layer_id, area_mm2)]."""
    made = []
    for i, (layer_id, netname) in enumerate(planes):
        z = add_plane(board, layer_id, netname, outline_mm, priority=i)
        made.append((netname, layer_id, z))
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    out = []
    for netname, layer_id, z in made:
        area = z.GetFilledArea() if hasattr(z, "GetFilledArea") else -1
        out.append((netname, layer_id, area))
    return out
