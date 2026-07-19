"""Stage-4 runner: apply P0 setup to the netted board, save, reload, verify."""
import pcbnew
from board_setup import setup_board, STACKUP_POLICY, FAB_PROFILE_PCBPOWER

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage3_nets.kicad_pcb"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4_setup.kicad_pcb"

board = pcbnew.LoadBoard(SRC)
setup_board(board, outline_wh_mm=(25.0, 25.0))
assert pcbnew.SaveBoard(OUT, board)

b2 = pcbnew.LoadBoard(OUT)
ds = b2.GetDesignSettings()
layers = ds.GetCopperLayerCount()
track  = round(pcbnew.ToMM(ds.m_TrackMinWidth), 3)
clear  = round(pcbnew.ToMM(ds.m_MinClearance), 3)
edges  = [d for d in b2.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
print("layers:", layers, "| min track:", track, "| min clearance:", clear,
      "| edge shapes:", len(edges))
ok = (layers == STACKUP_POLICY["layers"]
      and track == FAB_PROFILE_PCBPOWER["min_track_mm"]
      and clear == FAB_PROFILE_PCBPOWER["min_clearance_mm"]
      and len(edges) == 1)
print("STAGE4-SETUP SELFCHECK", "PASS" if ok else "FAIL")
