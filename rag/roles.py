"""roles.py - derive component ROLES from measurable properties (PURE, no pcbnew).

Replaces hardcoded reference designators. Nothing here keys on a ref name or
prefix: 'U1' is not special, 'R' does not mean resistor. Roles come from pad
counts, pin semantics and net membership, so a board with one MCU and a board
with a PMIC plus five sensors are handled by the same logic.

Verified brittleness this fixes: a second LLM emitted '100n' instead of
'100nF' and different ref numbering, which broke exact-string value matching
and the R1..R4 pull-up list.
"""
import re

IC_MIN_PADS = 6          # below this a part is treated as a discrete

# KNOWN GAP: pad count cannot separate an IC from a connector - a 24-pin
# connector reads as an IC. Placement treats connectors differently (board
# edge, orientation), so distinguishing them needs footprint-library data
# (footprint name/category), not netlist topology. Flagged, not guessed.
_SI = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
       "k": 1e3, "K": 1e3, "M": 1e6, "meg": 1e6, "G": 1e9}


def value_kind(text):
    """'C' | 'R' | 'L' | None from the unit letter. The netlist distinguishes a
    resistor from a capacitor by its unit, so a pull-down and a filter cap on
    the same signal-to-ground topology can be told apart without ref prefixes."""
    if not text:
        return None
    s = str(text).strip()
    if re.search(r"[Ff]$", s) or re.search(r"[pnuµ]\d*[Ff]?$", s):
        return "C"
    if re.search(r"[Rr]$|[Ωω]|ohm|Ohm", s) or re.search(r"^[\d.]+\s*[kKM]?$", s):
        return "R"
    if re.search(r"[Hh]$", s):
        return "L"
    return None


def parse_value(text):
    """'100nF'->1e-7, '100n'->1e-7, '4.7uF'->4.7e-6, '10k'->1e4, ''->None.
    Unit-agnostic: callers know whether they asked about a cap or a resistor."""
    if not text:
        return None
    s = str(text).strip().replace("Ω", "").replace("ohm", "").replace("Ohm", "")
    s = re.sub(r"[FfHh]$", "", s)                 # drop trailing unit letter
    m = re.match(r"^([\d.]+)\s*([pnuµmkKMG]|meg)?$", s)
    if m:
        v = float(m.group(1))
        return v * _SI.get(m.group(2), 1.0) if m.group(2) else v
    m = re.match(r"^(\d*)([pnuµmkKMG])(\d+)$", s)  # '4u7' style
    if m:
        whole = m.group(1) or "0"
        return float("%s.%s" % (whole, m.group(3))) * _SI[m.group(2)]
    return None


def classify_components(pad_counts, nets_meta, net_class, values=None):
    """Returns a role map derived from structure, not names.

    pad_counts: {ref: n_pads}          (measured from footprints)
    nets_meta:  {net: [(ref,pin,pinfunction,pintype)]}
    net_class:  {net: GND|POWER|ANALOG|SIGNAL}
    values:     {ref: '100nF'}         (optional, for decap vs bulk)
    """
    values = values or {}
    ics = sorted((r for r, n in pad_counts.items() if n >= IC_MIN_PADS),
                 key=lambda r: -pad_counts[r])
    discretes = [r for r in pad_counts if r not in ics]

    # which nets each discrete touches, by class
    touch = {}
    for net, nodes in nets_meta.items():
        cls = net_class.get(net, "SIGNAL")
        for ref, pin, _fn, _ty in nodes:
            if ref in pad_counts:
                touch.setdefault(ref, []).append((net, cls))

    roles = {r: "ic" for r in ics}
    rail_parts = []
    for r in discretes:
        classes = [c for _n, c in touch.get(r, [])]
        has_gnd = "GND" in classes
        has_rail = any(c in ("POWER", "ANALOG") for c in classes)
        has_sig = "SIGNAL" in classes
        kind = value_kind(values.get(r))
        if has_rail and has_gnd:
            if kind == "R":
                roles[r] = "divider"       # rail-to-ground resistor
            else:
                roles[r] = "rail_cap"      # decap or bulk - split by value below
                rail_parts.append(r)
        elif has_rail and has_sig:
            roles[r] = "pullup" if kind != "C" else "coupling"
        elif has_sig and has_gnd:
            roles[r] = "pulldown" if kind == "R" else "signal_cap"
        elif classes.count("SIGNAL") >= 2:
            roles[r] = "series"
        else:
            roles[r] = "other"

    # decap vs bulk: on each rail the smallest capacitance decouples a pin,
    # larger ones are bulk. Falls back to "all decaps" when values are absent.
    parsed = {r: parse_value(values.get(r)) for r in rail_parts}
    by_rail = {}
    for r in rail_parts:
        for net, cls in touch.get(r, []):
            if cls in ("POWER", "ANALOG"):
                by_rail.setdefault(net, []).append(r)
                break
    for net, parts in by_rail.items():
        vals = [parsed[p] for p in parts if parsed[p] is not None]
        if not vals:
            continue
        smallest = min(vals)
        for p in parts:
            if parsed[p] is not None and parsed[p] > smallest:
                roles[p] = "bulk"
            else:
                roles[p] = "decap"
    for r in rail_parts:
        roles.setdefault(r, "decap")
        if roles[r] == "rail_cap":
            roles[r] = "decap"

    return {"roles": roles, "ics": ics,
            "anchor": ics[0] if ics else None,
            "by_role": _invert(roles)}


def _invert(roles):
    out = {}
    for ref, role in roles.items():
        out.setdefault(role, []).append(ref)
    for k in out:
        out[k].sort()
    return out
