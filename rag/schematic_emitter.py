"""
schematic_emitter.py -- Module 4, Stages 4+5: connect via net-labels & emit.
Drives the validated SchematicBuilder from the placed component model.
Reuses builder's proven endpoints. Count-agnostic.

NC handling: the emitter owns WHICH pins are unconnected (model ground truth:
pd["net"] is None), and drives add_no_connect explicitly. It does NOT use the
builder's auto_no_connect_unused_pins() because this flow calls pin_endpoint on
every pin (to record endpoints), which pollutes that method's used-tracking.
"""

import power_wiring as pw

_POWER_HINTS = ("VDD", "VSS", "GND", "VCC", "3V3", "VBAT", "VREF", "VDDA")


def _is_power_net(name):
    up = name.upper()
    return any(up.startswith(h) or up == h for h in _POWER_HINTS)


def emit_schematic(components, placement, model, builder,
                   title="Auto Schematic", company="",
                   cap_values=None, region_cap_list=(),
                   region_x=26.67, region_y=170.18):
    endpoints = {}
    cap_values = cap_values or {}

    # --- 1. Place every component, record per-pin absolute endpoints ---
    for ref in sorted(components):
        comp = components[ref]
        if ref not in placement:
            # Not on the grid -> the POWER WIRING owns this component (it is a
            # decoupling cap, drawn inside a T-junction beside the pin it serves
            # or in the supply region). Skip it here; pw places it.
            continue
        x, y = placement[ref]
        if comp["kind"] == "ic":
            builder.add_ic_by_name(ref, comp["name"], x, y,
                                   value=comp.get("value") or comp["name"],
                                   footprint=comp.get("footprint") or "")
            endpoints[ref] = {num: builder.pin_endpoint(ref, num)
                              for num in comp["pins"]}
        else:
            val = comp.get("value") or comp["name"]
            if comp["name"] == "R":
                _ref, p1, p2 = builder.add_resistor(val, x, y)
            elif comp["name"] == "C":
                _ref, p1, p2 = builder.add_capacitor(val, x, y)
            else:
                _ref, p1, p2 = builder.add_capacitor(val, x, y)
            endpoints[ref] = {"1": p1, "2": p2, "_builder_ref": _ref}

    # --- 1b. POWER AUTO-WIRING -------------------------------------------
    # The routability rule decides, per IC, which supply rails can be DRAWN as
    # ST-style T-junctions and which must be LABELED (pins too crowded to wire).
    # Wired pins are then OWNED by the wiring: the label loop and the NC loop
    # must both skip them -- a no-connect dropped on a wired pin is honoured by
    # KiCad OVER the wire, silently disconnecting it.
    wired_pins = set()
    labeled_rails = {}
    step_idx = 0
    for ref in sorted(components):
        comp = components[ref]
        if comp["kind"] != "ic":
            continue
        rails = pw.supply_rails(comp)
        wired, labeled = pw.decide(comp, placement[ref], rails)
        for rail, stacks in wired.items():
            cval = cap_values.get(rail, "100nF")
            used, step_idx = pw.wire_rail(builder, rail, stacks, cval, step_idx)
            for num in used:
                wired_pins.add((ref, num))
        for rail in labeled:
            used = pw.label_rail(builder, rail, comp, placement[ref], rails[rail])
            for num in used:
                wired_pins.add((ref, num))
            labeled_rails.setdefault(rail, []).append(ref)

    region_caps = [(r, v) for r, v in region_cap_list if r in labeled_rails]
    if region_caps:
        pw.supply_region(builder, region_caps, region_x, region_y)

    # --- 2. Net-labels on every pin that is on a real net ---
    labels_placed = 0
    power_dropped = set()
    for ref in sorted(components):
        comp = components[ref]
        if ref not in endpoints:              # wiring owns this component
            continue
        for num, pd in comp["pins"].items():
            net = pd["net"]
            if not net:
                continue
            if (ref, num) in wired_pins:      # power wiring owns this pin
                continue
            lx, ly = endpoints[ref][num]
            builder.add_label(net, lx, ly)
            labels_placed += 1
            if _is_power_net(net) and net not in power_dropped:
                builder.add_power(net, lx, ly)
                power_dropped.add(net)

    # --- 3. No-connect on every IC pin with NO net (and not hidden) ---
    nc_placed = 0
    for ref in sorted(components):
        comp = components[ref]
        if comp["kind"] != "ic" or ref not in endpoints:
            continue
        for num, pd in comp["pins"].items():
            if (ref, num) in wired_pins:
                continue
            if pd["net"] is None and not pd["hidden"]:
                ex, ey = endpoints[ref][num]
                builder.add_no_connect(ex, ey)
                nc_placed += 1

    return {"labels_placed": labels_placed,
            "power_nets": sorted(power_dropped),
            "nc_placed": nc_placed,
            "wired_pins": len(wired_pins),
            "labeled_rails": sorted(labeled_rails),
            "endpoints": endpoints}
