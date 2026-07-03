"""
placement.py -- Module 4, Stage 3: auto-placement.
Non-overlapping sheet coordinates for all components. Count-agnostic.
ICs on a top row; passives on a grid below. Correct-first, not optimal.

ALL returned coordinates are snapped to KiCad's 1.27mm connection grid, so pin
endpoints and net-labels coincide exactly -- otherwise KiCad won't connect them
(off-grid pins/labels dangle). Symbol pin geometry is authored on 1.27mm, so
snapping the ORIGIN keeps every pin endpoint on-grid too.
"""

GRID = 1.27


def _snap(v, grid=GRID):
    return round(round(v / grid) * grid, 2)


def place_components(components, ic_pitch=80.0, ic_row_y=100.0,
                     passive_col_pitch=15.0, passive_row_pitch=20.0,
                     passive_cols=8, passive_start_x=40.0,
                     passive_top_margin=70.0):
    placement = {}
    ics = sorted(ref for ref, c in components.items() if c["kind"] == "ic")
    passives = sorted(ref for ref, c in components.items() if c["kind"] != "ic")

    for i, ref in enumerate(ics):
        placement[ref] = (_snap(passive_start_x + i * ic_pitch), _snap(ic_row_y))

    passive_row0_y = ic_row_y + passive_top_margin
    for idx, ref in enumerate(passives):
        col = idx % passive_cols
        row = idx // passive_cols
        x = _snap(passive_start_x + col * passive_col_pitch)
        y = _snap(passive_row0_y + row * passive_row_pitch)
        placement[ref] = (x, y)
    return placement


def _bbox(component, x, y):
    xs = [x + pd["x"] for pd in component["pins"].values()]
    ys = [y + pd["y"] for pd in component["pins"].values()]
    return (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)


def check_no_overlap(components, placement):
    boxes = {ref: _bbox(components[ref], x, y) for ref, (x, y) in placement.items()}
    refs = list(boxes)
    overlaps = []
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            ax1, ay1, ax2, ay2 = boxes[refs[i]]
            bx1, by1, bx2, by2 = boxes[refs[j]]
            if not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1):
                overlaps.append((refs[i], refs[j]))
    return overlaps


def summarize_placement(components, placement):
    lines = [f"Placed {len(placement)} components"]
    for r in sorted(r for r in placement if components[r]["kind"] == "ic"):
        lines.append(f"    IC {r} ({components[r]['name']}) at {placement[r]}")
    passives = [r for r in placement if components[r]["kind"] != "ic"]
    lines.append(f"    + {len(passives)} passives on grid")
    return "\n".join(lines)
