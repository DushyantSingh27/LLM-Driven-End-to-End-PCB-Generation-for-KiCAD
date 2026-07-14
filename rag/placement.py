"""
placement.py -- Module 4, Stage 3: auto-placement.

Non-overlapping sheet coordinates for all components. Count-agnostic.
ICs on a top row; passives on a grid below. Correct-first, not optimal.

ALL returned coordinates are snapped to KiCad's 1.27mm connection grid, so pin
endpoints and net-labels coincide exactly -- otherwise KiCad won't connect them
(off-grid pins/labels dangle). Symbol pin geometry is authored on 1.27mm, so
snapping the ORIGIN keeps every pin endpoint on-grid too.

POWER-WIRING OWNERSHIP
----------------------
Decoupling caps (one pin on a power rail, the other on GND) are NOT placed on
the passive grid: the power auto-wiring owns them, because each is drawn as part
of a T-junction immediately beside the supply pin it serves (ST convention), or
in the supply region for label-connected rails. Pass those refs as `skip=`.
Use power_cap_refs() to compute the set.

IC MARGIN
---------
Supply pins route OUTWARD, perpendicular to the edge they sit on. A left-edge
supply pin (VREF+ on the STM32L476) needs sheet space to its LEFT for its
junction, cap and power symbol -- routing it "up" instead runs the wire along the
pin column and silently shorts every pin above it. ic_origin_x leaves room for
that outward run.
"""

GRID = 1.27

# Sheet room a supply stack needs outboard of an IC edge:
#   junction 10.16 + power symbol 5.08 + margin 2.54
OUTWARD_ROUTING_NEED = 17.78

_POWER_HINTS = ("VDD", "VSS", "GND", "VCC", "3V3", "VBAT", "VREF", "VDDA")


def _snap(v, grid=GRID):
    return round(round(v / grid) * grid, 2)


def _is_power_net(name):
    if not name:
        return False
    up = name.upper()
    return any(up.startswith(h) or up == h for h in _POWER_HINTS)


def power_cap_refs(components):
    """{cap_ref: rail} for every DECOUPLING cap -- one pin on a power rail, the
    other on GND. These belong to the power wiring, not the passive grid.
    A cap from a SIGNAL to GND (e.g. the NRST cap) is NOT decoupling: it stays.
    """
    out = {}
    for ref, c in components.items():
        if c.get("kind") == "ic" or c.get("name") != "C":
            continue
        nets = [pd.get("net") for pd in c["pins"].values()]
        if len(nets) != 2:
            continue
        a, b = nets
        if a == "GND" and b and b != "GND" and _is_power_net(b):
            out[ref] = b
        elif b == "GND" and a and a != "GND" and _is_power_net(a):
            out[ref] = a
    return out


def place_components(components, ic_pitch=80.0, ic_row_y=100.0,
                     passive_col_pitch=15.0, passive_row_pitch=20.0,
                     passive_cols=8, ic_origin_x=50.0,
                     passive_start_x=None, passive_top_margin=70.0,
                     skip=None):
    """ICs on a row; passives on a grid below.

    ic_origin_x : x of the first IC -- leaves OUTWARD_ROUTING_NEED of sheet left
                  of its left edge for outward-routed supply stacks.
    skip        : refs the CALLER places itself (power wiring owns its caps).
    """
    if passive_start_x is None:
        passive_start_x = ic_origin_x
    skip = set(skip or ())
    placement = {}

    ics = sorted(ref for ref, c in components.items() if c["kind"] == "ic")
    passives = sorted(ref for ref, c in components.items()
                      if c["kind"] != "ic" and ref not in skip)

    for i, ref in enumerate(ics):
        placement[ref] = (_snap(ic_origin_x + i * ic_pitch), _snap(ic_row_y))

    passive_row0_y = ic_row_y + passive_top_margin
    for idx, ref in enumerate(passives):
        col = idx % passive_cols
        row = idx // passive_cols
        placement[ref] = (_snap(passive_start_x + col * passive_col_pitch),
                          _snap(passive_row0_y + row * passive_row_pitch))
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
