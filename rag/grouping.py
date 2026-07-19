"""grouping.py - P2: decap<->power-pad assignment from netlist facts.
Rule (source: STM32L476 datasheet power scheme): one 100nF per IC power pin;
non-100nF caps on a rail are bulk, clustered near the rail's pad group.
Pure netlist logic - runs under any Python (no pcbnew import)."""
import re


def parse_netlist_values(net_path):
    """{ref: value} - bounded scan inside each comp block (no adjacency assumption)."""
    vals = {}
    lines = open(net_path, "r", encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        m = re.search(r'\(comp \(ref "([^"]+)"\)', lines[i])
        if m:
            ref, val, j = m.group(1), None, i + 1
            while j < len(lines) and '(comp (ref' not in lines[j]:
                vm = re.search(r'\(value "([^"]+)"\)', lines[j])
                if vm:
                    val = vm.group(1)
                    break
                j += 1
            if val is None:
                raise RuntimeError("comp %s: no value before next comp" % ref)
            vals[ref] = val
        i += 1
    return vals


def is_rail(netname):
    return netname.startswith("/V") or netname == "VDDA"


RAIL_POLICY = {
    # VDD12: datasheet states NO external decoupling required (SMPS bypass
    # rail). C15/C16 in the benchmark are a generation-stage over-decoupling
    # FINDING (upstream fix: RAG must extract per-rail cap requirements).
    # per_rail here means: place the existing caps as one rail cluster.
    "/VDD12": "per_rail",
}


def assign_decaps(nets, values, ic_refs=("U1", "U2"), decap_value="100nF",
                  rail_policy=None):
    """For each rail: pair decap-value caps 1:1 with IC power pads; rest = bulk.
    nets: [(netname, [(ref, pin), ...])]  (from parse_netlist_nets)
    Returns {rail: {"pairs": [((ic, pin), cap)], "bulk": [caps],
                    "spare_caps": [...], "unpaired_pads": [...]}}"""
    if rail_policy is None:
        rail_policy = RAIL_POLICY
    out = {}
    for netname, members in nets:
        if not is_rail(netname):
            continue
        policy = rail_policy.get(netname, "per_pin")
        caps = sorted({r for r, _ in members if r.startswith("C")},
                      key=lambda r: int(r[1:]))
        pads = sorted([(r, p) for r, p in members if r in ic_refs])
        decaps = [c for c in caps if values.get(c) == decap_value]
        bulk = [c for c in caps if values.get(c) != decap_value]
        pairs, spare = [], list(decaps)
        unpaired = []
        for pad in pads:
            if spare:
                pairs.append((pad, spare.pop(0)))
            else:
                unpaired.append(pad)
        # rails whose only cap is non-100nF (VREF+, VDDA, etc.): pair bulk 1:1
        if not decaps and bulk and pads:
            b = list(bulk)
            pairs, unpaired, bulk = [], [], []
            for pad in pads:
                if b:
                    pairs.append((pad, b.pop(0)))
                else:
                    unpaired.append(pad)
            bulk = b
        if policy == "per_rail" and unpaired and (pairs or bulk):
            # rail-level decoupling: remaining pads share the rail cap group
            pairs += [(pad, None) for pad in unpaired]
            unpaired = []
        out[netname] = {"pairs": pairs, "bulk": bulk, "policy": policy,
                        "spare_caps": spare, "unpaired_pads": unpaired}
    return out
