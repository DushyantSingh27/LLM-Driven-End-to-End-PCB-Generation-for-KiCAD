"""Stage-8 runner: pour GND/VDD planes on the placed board, save, reload, verify."""
import pcbnew
from board_builder import save_board
from zones import pour_planes, PLANE_POLICY
from placement_engine import POLICY

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.kicad_pcb"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage8_pours.kicad_pcb"

board = pcbnew.LoadBoard(SRC)
print("zones before:", len(list(board.Zones())))
res = pour_planes(board, POLICY["board"])
for netname, layer, area in res:
    print("  poured", netname, "on layer", layer, "| filled area (internal units):", area)
assert save_board(board, OUT)

b2 = pcbnew.LoadBoard(OUT)
zs = list(b2.Zones())
print("=== after reload ===")
print("zones:", len(zs))
ok = len(zs) == 2
for z in zs:
    filled = z.IsFilled() if hasattr(z, "IsFilled") else "?"
    print("  net:", z.GetNetname(), "| layer:", z.GetLayer(),
          "| filled:", filled, "| priority:", z.GetAssignedPriority())
    if not z.GetNetname() or not filled:
        ok = False
print("STAGE8 SELFCHECK", "PASS" if ok else "FAIL")
