"""board_setup.py - P0: stackup, provisional Edge.Cuts outline, Tier-1 DFM floors.
Verified 9.0 surface: SetCopperLayerCount, m_TrackMinWidth/m_MinClearance/
m_ViasMinSize/m_MinThroughDrill, SetBoardThickness, PCB_SHAPE+SHAPE_T_RECTANGLE
on Edge_Cuts (layer id 25). Netclasses deferred to resolver (9.0 API moved).
All numbers are DATA (fab profile / policy dict), never inline constants."""
import pcbnew

# Tier-1 manufacturability floors - PCB Power DFM reference table (mm)
FAB_PROFILE_PCBPOWER = {
    "min_track_mm":    0.09,
    "min_clearance_mm": 0.09,
    "min_via_mm":      0.45,   # pad for 0.20 drill + annular; refined by resolver
    "min_drill_mm":    0.20,
}

# Stackup policy: fine-pitch area-array (<=0.5mm pitch) forces 4 layers
STACKUP_POLICY = {"layers": 4, "thickness_mm": 1.6}


def setup_board(board, outline_wh_mm, origin_mm=(20.0, 20.0),
                fab=FAB_PROFILE_PCBPOWER, stackup=STACKUP_POLICY):
    """Apply stackup + Tier-1 floors, draw provisional rectangular outline.
    outline_wh_mm: (width, height). Returns the PCB_SHAPE outline object."""
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(stackup["layers"])
    ds.SetBoardThickness(pcbnew.FromMM(stackup["thickness_mm"]))
    # Default netclass clearance must match the fab floor: KiCad's stock
    # 0.2mm default DRC-fails fine-pitch packages (WLCSP 0.4mm pitch has
    # 0.175mm pad gaps). Verified route: m_NetSettings.GetDefaultNetclass().
    ncdef = ds.m_NetSettings.GetDefaultNetclass()
    ncdef.SetClearance(pcbnew.FromMM(fab["min_clearance_mm"]))
    ds.m_TrackMinWidth   = pcbnew.FromMM(fab["min_track_mm"])
    ds.m_MinClearance    = pcbnew.FromMM(fab["min_clearance_mm"])
    ds.m_ViasMinSize     = pcbnew.FromMM(fab["min_via_mm"])
    ds.m_MinThroughDrill = pcbnew.FromMM(fab["min_drill_mm"])

    x0, y0 = origin_mm
    w, h = outline_wh_mm
    sh = pcbnew.PCB_SHAPE(board)
    sh.SetShape(pcbnew.SHAPE_T_RECTANGLE)
    sh.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y0)))
    sh.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x0 + w), pcbnew.FromMM(y0 + h)))
    sh.SetLayer(pcbnew.Edge_Cuts)
    sh.SetWidth(pcbnew.FromMM(0.1))
    board.Add(sh)
    return sh
