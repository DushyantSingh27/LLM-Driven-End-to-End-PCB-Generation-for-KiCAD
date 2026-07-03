"""
schematic_emitter.py -- Module 4, Stages 4+5: connect via net-labels & emit.
Drives the validated SchematicBuilder from the placed component model.
Reuses builder's proven endpoints. Count-agnostic.

NC handling: the emitter owns WHICH pins are unconnected (model ground truth:
pd["net"] is None), and drives add_no_connect explicitly. It does NOT use the
builder's auto_no_connect_unused_pins() because this flow calls pin_endpoint on
every pin (to record endpoints), which pollutes that method's used-tracking.
"""

_POWER_HINTS = ("VDD", "VSS", "GND", "VCC", "3V3", "VBAT", "VREF", "VDDA")


def _is_power_net(name):
    up = name.upper()
    return any(up.startswith(h) or up == h for h in _POWER_HINTS)


def emit_schematic(components, placement, model, builder,
                   title="Auto Schematic", company=""):
    endpoints = {}

    # --- 1. Place every component, record per-pin absolute endpoints ---
    for ref in sorted(components):
        comp = components[ref]
        x, y = placement[ref]
        if comp["kind"] == "ic":
            builder.add_ic_by_name(ref, comp["name"], x, y,
                                   value=comp.get("value") or comp["name"])
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

    # --- 2. Net-labels on every pin that is on a real net ---
    labels_placed = 0
    power_dropped = set()
    for ref in sorted(components):
        comp = components[ref]
        for num, pd in comp["pins"].items():
            net = pd["net"]
            if not net:
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
        if comp["kind"] != "ic":
            continue
        for num, pd in comp["pins"].items():
            if pd["net"] is None and not pd["hidden"]:
                ex, ey = endpoints[ref][num]
                builder.add_no_connect(ex, ey)
                nc_placed += 1

    return {"labels_placed": labels_placed,
            "power_nets": sorted(power_dropped),
            "nc_placed": nc_placed,
            "endpoints": endpoints}
