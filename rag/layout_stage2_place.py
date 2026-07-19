"""Stage-2 runner: place all netlist components on a grid, save, reload, verify."""
import pcbnew
from board_builder import place_all_grid

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage2_grid.kicad_pcb"

EXPECT_REFS = (["C%d" % i for i in range(1, 17)]
               + ["R%d" % i for i in range(1, 5)] + ["U1", "U2"])
EXPECT_PADS = 16 * 2 + 4 * 2 + 72 + 14   # = 126

board, comps = place_all_grid(NET, OUT)
print("parsed comps:", len(comps))

b2 = pcbnew.LoadBoard(OUT)
fps = b2.GetFootprints()
refs = sorted(f.GetReference() for f in fps)
pads = sum(f.GetPadCount() for f in fps)
print("reloaded: footprints=", len(fps), "total pads=", pads)

ok_n    = len(fps) == 22
ok_refs = refs == sorted(EXPECT_REFS)
ok_pads = pads == EXPECT_PADS
print("refs match:", ok_refs, "| pads match:", ok_pads, "(expect %d)" % EXPECT_PADS)
if not ok_refs:
    print("  missing:", sorted(set(EXPECT_REFS) - set(refs)))
    print("  extra:  ", sorted(set(refs) - set(EXPECT_REFS)))
print("STAGE2 SELFCHECK", "PASS" if (ok_n and ok_refs and ok_pads) else "FAIL")
