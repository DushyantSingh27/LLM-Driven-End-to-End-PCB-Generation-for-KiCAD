"""Probe: why does pouring crash on an in-memory board?
Flushed prints so the last line before a hard crash localises the failure."""
import pcbnew
from board_builder import place_all_grid, bind_nets, save_board
from netlist_reader import parse_netlist_nets, parse_netlist_nets_meta
from board_setup import setup_board
from grouping import parse_netlist_values, assign_decaps
from placement_engine import place_all
from legalize import legalize
from design_rules import build_rule_table, plane_candidates
from rules_apply import apply_rules
from zones import add_plane

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.net"
TMP = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_pour_tmp.kicad_pcb"

def say(*a): print(*a, flush=True)

say("1. build + bind")
board, comps = place_all_grid(NET, TMP)
nets = parse_netlist_nets(NET)
bind_nets(board, nets)
say("2. setup + place + legalize")
setup_board(board, outline_wh_mm=(25.0, 25.0))
meta = parse_netlist_nets_meta(NET)
place_all(board, assign_decaps(nets, parse_netlist_values(NET)))
legalize(board)
say("3. rules")
net_class, class_rules, prov = build_rule_table(meta)
apply_rules(board, net_class, class_rules)
gnet, pnet = plane_candidates(net_class, meta)
say("   planes:", gnet, pnet)

say("4. connectivity API present?",
    [s for s in dir(board) if "onnectivit" in s])
try:
    board.BuildConnectivity()
    say("   BuildConnectivity() OK")
except Exception as e:
    say("   BuildConnectivity failed:", repr(e))

say("5. add zone outlines (no fill yet)")
add_plane(board, pcbnew.In1_Cu, gnet, (20.0, 20.0, 45.0, 45.0), priority=0)
add_plane(board, pcbnew.In2_Cu, pnet, (20.0, 20.0, 45.0, 45.0), priority=1)
say("   zones added:", len(list(board.Zones())))

say("6. FILL  <-- if output stops here, the filler is the crash point")
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
say("   fill returned")

say("7. save")
say("   save rc:", save_board(board, TMP))
b2 = pcbnew.LoadBoard(TMP)
say("   reload: zones=", len(list(b2.Zones())),
    "| nets=", b2.GetNetCount(),
    "| In1 type=", b2.GetLayerType(pcbnew.In1_Cu))
say("PROBE COMPLETE")
