"""
netlist_parser.py -- Module 4, Stage 1: connectivity extraction.
Reads any SKiDL circuit into a generic, count-agnostic structure.
"""

_SKIP_NETS = {"__NOCONNECT"}


def parse_circuit(circuit):
    parts = {}
    for p in circuit.parts:
        lib = getattr(p.lib, "filename", None) if getattr(p, "lib", None) else None
        parts[p.ref] = {
            "name": p.name,
            "library": lib,
            "value": getattr(p, "value", None),
            "pins": [str(pin.num) for pin in p.pins],
        }

    nets = {}
    pin_net = {}
    nc_pins = []
    for net in circuit.nets:
        members = [(pin.part.ref, str(pin.num)) for pin in net.get_pins()]
        if net.name in _SKIP_NETS:
            nc_pins.extend(members)
            continue
        if not members:
            continue
        nets[net.name] = members
        for ref, num in members:
            pin_net[(ref, num)] = net.name

    return {"parts": parts, "nets": nets, "pin_net": pin_net, "nc_pins": nc_pins}


def summarize(model):
    from collections import Counter
    lines = [f"Parts: {len(model['parts'])}"]
    by_name = Counter(p["name"] for p in model["parts"].values())
    for name, n in sorted(by_name.items()):
        lines.append(f"    {name}: {n}")
    lines.append(f"Real nets: {len(model['nets'])}")
    lines.append(f"NC pins: {len(model['nc_pins'])}")
    total_conn = sum(len(v) for v in model["nets"].values())
    lines.append(f"Pin-connections across real nets: {total_conn}")
    return "\n".join(lines)
