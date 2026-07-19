"""Stage-3 runner: grid-place all parts, bind every pad to its net, save,
then reload and independently verify every netlist node against the board."""
import pcbnew
from board_builder import place_all_grid, parse_netlist_nets, bind_nets, save_board

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage3_nets.kicad_pcb"

board, comps = place_all_grid(NET, OUT)   # places 22 parts, saves once
nets = parse_netlist_nets(NET)
n_nets, n_pads = bind_nets(board, nets)
rc = save_board(board, OUT)               # re-save with nets bound
print("nets created:", n_nets, "| pads bound:", n_pads, "| save rc:", rc)

# --- independent verification pass: reload and check every node ---
b2 = pcbnew.LoadBoard(OUT)
padmap = {}
for fp in b2.GetFootprints():
    for p in fp.Pads():
        padmap.setdefault((fp.GetReference(), p.GetName()), []).append(p.GetNetname())

missing, wrong = [], []
total_nodes = 0
for netname, members in nets:
    for ref, pin in members:
        total_nodes += 1
        got = padmap.get((ref, pin))
        if got is None:
            missing.append((netname, ref, pin))
        elif not all(g == netname for g in got):
            wrong.append((netname, ref, pin, got))

print("nodes checked:", total_nodes, "| missing:", len(missing), "| wrong-net:", len(wrong))
for item in (missing + wrong)[:10]:
    print("  FAIL:", item)
print("STAGE3 SELFCHECK", "PASS" if (not missing and not wrong and total_nodes > 0) else "FAIL")
