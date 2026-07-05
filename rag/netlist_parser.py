"""
netlist_parser.py -- Module 4, Stage 1: connectivity extraction.
Reads any SKiDL circuit into a generic, count-agnostic structure.

Canonicalization: SKiDL may give ONE electrical net several names (aliases)
when the netlist ties rails together (e.g. imu_vdd += vdd). Nets sharing an
identical pin-set are collapsed to a single canonical name, so downstream
labels produce ONE connected rail in KiCad instead of fragmenting it.
"""

_SKIP_NETS = {"__NOCONNECT"}

# Conventional rail names preferred as the canonical name when present.
_PREFERRED = ("GND", "VDD_3V3", "VDD", "VCC", "3V3", "VSS", "VDDA")


def _canonicalize(raw_nets):
    """raw_nets: list of (name, [(ref,pin),...]). Collapse identical pin-sets."""
    from collections import defaultdict
    groups = defaultdict(list)
    members_by_key = {}
    for name, members in raw_nets:
        key = frozenset(members)
        groups[key].append(name)
        members_by_key[key] = members

    nets = {}
    name_map = {}
    for key, names in groups.items():
        pref = next((p for p in _PREFERRED if p in names), None)
        canonical = pref if pref else sorted(names)[0]
        nets[canonical] = members_by_key[key]
        for n in names:
            name_map[n] = canonical
    return nets, name_map


def parse_circuit(circuit):
    parts = {}
    for p in circuit.parts:
        lib = getattr(p.lib, "filename", None) if getattr(p, "lib", None) else None
        parts[p.ref] = {
            "name": p.name,
            "library": lib,
            "value": getattr(p, "value", None),
            "footprint": getattr(p, "footprint", None) or None,
            "pins": [str(pin.num) for pin in p.pins],
        }

    # Collect raw nets (may contain aliased duplicates), separate NC.
    raw_nets = []
    nc_pins = []
    for net in circuit.nets:
        members = [(pin.part.ref, str(pin.num)) for pin in net.get_pins()]
        if net.name in _SKIP_NETS:
            nc_pins.extend(members)
            continue
        if not members:
            continue
        raw_nets.append((net.name, members))

    # Collapse aliased nets to one canonical name each.
    nets, name_map = _canonicalize(raw_nets)

    # Build reverse lookup on the CANONICAL names.
    pin_net = {}
    for cname, members in nets.items():
        for ref, num in members:
            pin_net[(ref, num)] = cname

    return {
        "parts": parts,
        "nets": nets,
        "pin_net": pin_net,
        "nc_pins": nc_pins,
        "name_map": name_map,   # orig net name -> canonical (for traceability)
    }


def summarize(model):
    from collections import Counter
    lines = [f"Parts: {len(model['parts'])}"]
    by_name = Counter(p["name"] for p in model["parts"].values())
    for name, n in sorted(by_name.items()):
        lines.append(f"    {name}: {n}")
    lines.append(f"Distinct electrical nets: {len(model['nets'])}")
    lines.append(f"NC pins: {len(model['nc_pins'])}")
    total_conn = sum(len(v) for v in model["nets"].values())
    lines.append(f"Pin-connections across real nets: {total_conn}")
    # report any merges
    merges = {}
    for orig, canon in model["name_map"].items():
        if orig != canon:
            merges.setdefault(canon, []).append(orig)
    if merges:
        lines.append("Merged (aliased) nets:")
        for canon, origs in merges.items():
            lines.append(f"    {canon} <- {sorted(origs)}")
    return "\n".join(lines)
