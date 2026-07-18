"""
power_wiring.py -- ST-style power auto-wiring.

Draws supply rails as ST does: a T-junction per supply pin --
[power symbol] -> wire -> (junction, cap taps here) -> supply pin, cap low side
to a local GND symbol. The cap sits immediately beside the pin it serves.

Not every rail CAN be drawn that way. On a dense part (STM32L476: 9 supply pins
at 2.54mm on one edge) the T-junctions collide or their wires cross other pins.
So we decide per rail:

    ROUTABILITY RULE
    Wire a rail if its stacks fit the free space between neighbouring rails'
    pins AND cross no other pin. Otherwise LABEL it and put its caps in a
    supply region.

Geometry decides -- so a crowded MCU gets labels where it must, a sparse sensor
gets real wires. Both are correct, and ST mixes the two freely.

EDGE-AWARE: a stack exits OUTWARD, perpendicular to its pin's edge. Routing "up"
from a LEFT-edge pin runs along the pin column and silently shorts every pin
above it -- exactly how VREF+ shorted NRST and BOOT0, which ERC called clean.

COLLISION RULES (each learned from a real bug):
  * CAP_OFFSET != STACK_PITCH, else a cap's tap wire lands on the neighbouring
    stack's junction and fuses two rails.
  * Each STEPPED stack gets its own jog track, else two jogs share a y and fuse.
  * Exactly ONE power driver per net sheet-wide (the builder's power_nets_used
    set gives this); two PWR_FLAGs on one net is a pin_to_pin error.
  * Every rail needs a NET LABEL, else ST-specific rails are anonymous power
    nets KiCad cannot tell apart.
"""

GRID = 1.27
STACK_PITCH = 7.62
CAP_OFFSET = 6.35        # MUST differ from STACK_PITCH
OUT_RUN = 10.16
PWR_RUN = 5.08

_POWER_HINTS = ("VDD", "VSS", "GND", "VCC", "3V3", "VBAT", "VREF", "VDDA")


def snap(v, grid=GRID):
    return round(round(v / grid) * grid, 2)


def is_power_net(name):
    if not name:
        return False
    up = name.upper()
    return any(up.startswith(h) or up == h for h in _POWER_HINTS)


def pin_edge(comp, num):
    pd = comp["pins"][num]
    xs = [p["x"] for p in comp["pins"].values()]
    ys = [p["y"] for p in comp["pins"].values()]
    hw = max(abs(min(xs)), abs(max(xs)))
    hh = max(abs(min(ys)), abs(max(ys)))
    if abs(abs(pd["x"]) - hw) < 0.01:
        return "LEFT" if pd["x"] < 0 else "RIGHT"
    if abs(abs(pd["y"]) - hh) < 0.01:
        return "TOP" if pd["y"] > 0 else "BOTTOM"
    return "TOP"


def supply_rails(comp, exclude=("GND",)):
    """{rail: [pins]} of power-input rails. GND excluded: it is scattered over
    the part and every cap, so it always uses local GND symbols, never a drawn
    net -- which is what ST does too."""
    rails = {}
    for num, pd in comp["pins"].items():
        net = pd.get("net")
        if not net or net in exclude or not is_power_net(net):
            continue
        rails.setdefault(net, []).append(num)
    return rails


def _crosses(oy, py, edge):
    if edge == "TOP":
        return py - 24.13 <= oy <= py
    if edge == "BOTTOM":
        return py <= oy <= py + 24.13
    return False


def decide(comp, placement_xy, rails):
    """Returns ({rail: [(pin, px, py, stack_x, edge)]}, [labeled_rails])."""
    icx, icy = placement_xy

    def abs_xy(num):
        pd = comp["pins"][num]
        return snap(icx + pd["x"]), snap(icy - pd["y"])

    all_pins = {n: abs_xy(n) for n in comp["pins"]}
    wired, labeled, taken = {}, [], []

    # simplest rails first, so a greedy multi-pin rail cannot steal a
    # single-pin rail's natural slot
    for rail, pins in sorted(rails.items(), key=lambda kv: len(kv[1])):
        pins_sorted = sorted(pins, key=lambda n: abs_xy(n)[0])
        edge = pin_edge(comp, pins_sorted[0])

        if edge in ("LEFT", "RIGHT") and len(pins_sorted) == 1:
            num = pins_sorted[0]
            px, py = abs_xy(num)
            wired[rail] = [(num, px, py, px, edge)]
            continue

        placed, ok, prev = [], True, None
        for num in pins_sorted:
            px, py = abs_xy(num)
            sx = snap(px) if prev is None else snap(max(px, prev + STACK_PITCH))
            for t in taken:
                if abs(sx - t) < STACK_PITCH:
                    sx = snap(t + STACK_PITCH)
            for onum, (ox, oy) in all_pins.items():
                if onum in pins_sorted:
                    continue
                if abs(ox - sx) < 0.01 and _crosses(oy, py, edge):
                    ok = False
                    break
            if not ok:
                break
            placed.append((num, px, py, sx, edge))
            prev = sx

        if ok and placed and len(placed) > 1:
            spill = max(abs(s - p) for _, p, _, s, _ in placed)
            if spill > STACK_PITCH * 1.5:
                ok = False       # crowded out: would snake wires across the part

        if ok and placed:
            wired[rail] = placed
            taken += [p[3] for p in placed]
        else:
            labeled.append(rail)
    return wired, labeled


def wire_rail(builder, rail, stacks, cap_value, step_start=0):
    used, step_idx = [], step_start
    for num, px, py, sx, edge in stacks:
        if edge == "LEFT":
            _t_horizontal(builder, rail, px, py, cap_value, -1)
        elif edge == "RIGHT":
            _t_horizontal(builder, rail, px, py, cap_value, +1)
        else:
            stepped = abs(sx - px) > 0.01
            _t_vertical(builder, rail, px, py, sx, cap_value,
                        step_idx if stepped else 0)
            if stepped:
                step_idx += 1
        used.append(num)
    return used, step_idx


def _t_vertical(builder, rail, px, py, sx, cval, step_idx):
    step_y = snap(py - 5.08 + step_idx * 2.54)
    jy = snap(py - 19.05)
    pwry = snap(py - 24.13)
    if abs(sx - px) > 0.01:
        builder.add_wire(px, py, px, step_y)
        builder.add_wire(px, step_y, sx, step_y)
        builder.add_wire(sx, step_y, sx, jy)
    else:
        builder.add_wire(px, py, sx, jy)
    builder.add_junction(sx, jy)
    # label ON a wire that always exists: the pin->junction vertical segment
    # (jy+2.54 sits on it). The old jy-2.54 spot lay on the power-symbol segment,
    # which is now conditional -> would dangle when the net is already driven.
    builder.add_label(rail, sx, snap(jy + 2.54))
    capx = snap(sx - CAP_OFFSET)
    _r, ctop, cbot = builder.add_capacitor(cval, capx, snap(jy + 3.81), rot=0)
    builder.add_wire(ctop[0], ctop[1], sx, jy)
    # Extend to a power symbol ONLY if this net still needs a driver. If it is
    # already driven elsewhere (e.g. VDD_3V3 driven at another IC or in the
    # supply region), add_power would no-op and the wire-to-symbol would dangle.
    # The label above already ties the stack into the net.
    if rail not in builder.power_nets_used:
        builder.add_wire(sx, jy, sx, pwry)
        builder.add_power(rail, sx, pwry)
    gy = snap(cbot[1] + 2.54)
    builder.add_wire(cbot[0], cbot[1], cbot[0], gy)
    builder.add_power("GND", cbot[0], gy)


def _t_horizontal(builder, rail, px, py, cval, sign):
    jx = snap(px + sign * OUT_RUN)
    pwrx = snap(jx + sign * PWR_RUN)
    builder.add_wire(px, py, jx, py)
    builder.add_junction(jx, py)
    # label on the pin->junction segment (toward the pin), always present
    builder.add_label(rail, snap(jx - sign * 2.54), py)
    _r, ctop, cbot = builder.add_capacitor(cval, jx, snap(py + 6.35), rot=0)
    builder.add_wire(ctop[0], ctop[1], jx, py)
    if rail not in builder.power_nets_used:
        builder.add_wire(jx, py, pwrx, py)
        builder.add_power(rail, pwrx, py)
    gy = snap(cbot[1] + 2.54)
    builder.add_wire(cbot[0], cbot[1], cbot[0], gy)
    builder.add_power("GND", cbot[0], gy)


def label_rail(builder, rail, comp, placement_xy, pins):
    icx, icy = placement_xy
    used = []
    for num in pins:
        pd = comp["pins"][num]
        px, py = snap(icx + pd["x"]), snap(icy - pd["y"])
        end = snap(py - 3.81)
        builder.add_wire(px, py, px, end)
        builder.add_label(rail, px, end)
        used.append(num)
    return used


def supply_region(builder, caps, start_x, start_y,
                  col_pitch=15.24, row_pitch=25.40, per_row=6):
    for i, (rail, value) in enumerate(caps):
        cx = snap(start_x + (i % per_row) * col_pitch)
        cy = snap(start_y + (i // per_row) * row_pitch)
        _r, ctop, cbot = builder.add_capacitor(value, cx, cy, rot=0)
        lab_y = snap(ctop[1] - 3.81)
        builder.add_wire(ctop[0], ctop[1], ctop[0], lab_y)
        builder.add_label(rail, ctop[0], lab_y)
        builder.add_power(rail, ctop[0], lab_y)
        gy = snap(cbot[1] + 2.54)
        builder.add_wire(cbot[0], cbot[1], cbot[0], gy)
        builder.add_power("GND", cbot[0], gy)
