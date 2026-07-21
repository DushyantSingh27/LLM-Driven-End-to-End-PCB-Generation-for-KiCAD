"""Probe: do courtyards track footprint positions on an IN-MEMORY board,
or only after save+reload? Decides the layout_pipeline L4->L5 fix."""
import pcbnew
from board_builder import place_all_grid

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"
TMP = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\probe_tmp.kicad_pcb"


def report(board, label):
    print("=== %s ===" % label)
    for ref in ("C1", "C5", "U1"):
        fp = [f for f in board.GetFootprints() if f.GetReference() == ref][0]
        p = fp.GetPosition()
        cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        print(ref, "| pos:", round(pcbnew.ToMM(p.x), 1), round(pcbnew.ToMM(p.y), 1),
              "| courtyard: L", round(pcbnew.ToMM(cy.GetLeft()), 1),
              "T", round(pcbnew.ToMM(cy.GetTop()), 1),
              "W", round(pcbnew.ToMM(cy.GetWidth()), 2),
              "H", round(pcbnew.ToMM(cy.GetHeight()), 2))


board, comps = place_all_grid(NET, TMP)
report(board, "IN-MEMORY, right after place_all_grid")
b2 = pcbnew.LoadBoard(TMP)
report(b2, "RELOADED from the file just saved")
