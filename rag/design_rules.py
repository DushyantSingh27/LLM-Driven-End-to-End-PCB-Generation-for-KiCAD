"""design_rules.py - the design-rules resolver (PURE logic, no pcbnew).

Three tiers, resolved as: final = max(tier1_floor, tier2_requirement),
with per-value provenance so every number can be traced to its source.

  Tier 1  FAB_PROFILE   - manufacturability floors (fabricator spec). SOURCED.
  Tier 2  ELECTRICAL    - current-driven widths, IPC-2221. Needs per-net current;
                          class defaults used when unknown, tagged unverified.
  Tier 3  CONVENTIONS   - house/ST qualitative rules (consumed elsewhere).

Classification is DERIVED from netlist pin semantics (pintype/pinfunction),
never from net-name string matching - names vary per generator (verified: a
non-Claude model emitted VSS/VDD/VREF+ instead of GND/VDD_3V3/VREF_PLUS).
"""

# ---------------------------------------------------------------- Tier 1
FAB_PROFILE_PCBPOWER = {
    "name": "pcbpower",
    "min_track_mm": 0.09,       # PCB Power DFM: min trace width, 1oz Cu
    "min_clearance_mm": 0.09,   # PCB Power DFM: min trace-to-trace spacing
    "min_drill_mm": 0.20,       # PCB Power DFM: min PTH drill
    "min_annular_ring_mm": 0.125,  # UNVERIFIED default; PCB Power says "meets
                                   # minimum" without a number - confirm with fab
}

# ---------------------------------------------------------------- Tier 2
COPPER_WEIGHT_OZ = 1.0
DELTA_T_C = 10.0            # allowable temperature rise, conservative default

# Current per class when the netlist carries no current data. These are
# DEFAULTS, not measurements - every value resolved from them is tagged
# "default-unverified" in its provenance.
CLASS_DEFAULT_CURRENT_A = {
    "GND":     0.5,
    "POWER":   0.5,
    "ANALOG":  0.05,
    "SIGNAL":  0.05,
}

# PRACTICAL minimum width: the fab floor (0.09mm) is a yield cliff - designing
# at the absolute minimum leaves no margin for etch variation. This is a POLICY
# choice, not a sourced value; raise/lower per fab conversation.
PRACTICAL_MIN_TRACK_MM = 0.15

# Extra clearance by class (Tier 3 style policy, applied as a floor)
# Clearance per class. All values are the fabricator floor: at 3.3V there is
# no electrical clearance requirement anywhere near these numbers (creepage and
# clearance bind at far higher potentials), so manufacturability IS the binding
# constraint. An earlier POWER/ANALOG value of 0.15mm was invented margin and
# was measured to cost four real connections (U2-2, U2-5, U2-6, U2-8) with no
# source behind it. Raise these only from a sourced rule - a datasheet, a fab
# spec, or a voltage calculation.
CLASS_MIN_CLEARANCE_MM = {
    "GND":     0.09,
    "POWER":   0.09,
    "ANALOG":  0.09,
    "SIGNAL":  0.09,
}


def router_clearance_mm(clearance_mm, hole_clearance_mm, via_drill_mm,
                        via_dia_mm):
    """Clearance to hand an autorouter that only understands copper-to-copper.

    KiCad enforces a separate hole-to-copper rule which the Specctra DSN does
    not carry, so a router optimising to copper clearance alone produces hole
    violations (measured: 7 after a routing import). Inflating the copper
    clearance we export so that satisfying it also satisfies the hole rule:
        hole_r + obs_r + hole_clearance  <=  via_r + obs_r + exported_clearance
    which reduces to the expression below, independent of obstacle size."""
    hole_r, via_r = via_drill_mm / 2.0, via_dia_mm / 2.0
    return max(clearance_mm, hole_clearance_mm + hole_r - via_r)


def ipc2221_width_mm(current_a, delta_t_c=DELTA_T_C,
                     copper_oz=COPPER_WEIGHT_OZ, external=True):
    """IPC-2221 trace width for a given current.
    A[mils^2] = (I / (k * dT^0.44))^(1/0.725);  width = A / (1.378 * oz)
    k = 0.048 external, 0.024 internal."""
    k = 0.048 if external else 0.024
    area_mils2 = (current_a / (k * (delta_t_c ** 0.44))) ** (1.0 / 0.725)
    width_mils = area_mils2 / (1.378 * copper_oz)
    return width_mils * 0.0254


# ------------------------------------------------------- classification
# Pin-function families. Classification uses pinfunction as a FIRST-CLASS
# signal, not just pintype - verified against real netlist data:
#   - U1 VREF+ is pintype "input" (NOT power_in); semantics live in pinfunction
#   - GND carries a MIX: some VSS pins power_in, some passive. Relying on
#     pintype alone would misclassify a symbol whose ground pins are all
#     passive, silently turning a plane net into a routed signal.
# Order of evaluation matters: VSSA starts with VSS (ground, not analog);
# VDDA starts with VDD (analog, not generic power) - so GROUND is tested
# first, then ANALOG, then POWER.
GROUND_FUNCTION_TOKENS = ("GND", "VSS", "AGND", "DGND")
ANALOG_FUNCTION_TOKENS = ("VDDA", "VREF", "AREF", "AVDD", "AVCC", "VSSA_REF")
POWER_FUNCTION_TOKENS = ("VDD", "VCC", "VBAT", "VIN", "VBUS", "VPP")


def _pintypes(node):
    """pintype strings are compound, e.g. 'bidirectional+no_connect'."""
    _, _, _, pt = node
    return set((pt or "").split("+"))


def _matches(functions, tokens):
    return any(f.startswith(tok) for f in functions for tok in tokens)


def classify_nets(nets_with_meta):
    """nets_with_meta: {netname: [(ref, pin, pinfunction, pintype), ...]}
    Returns {netname: class} in GND/POWER/ANALOG/SIGNAL.
    Derived from pin semantics (pinfunction + pintype) - never net names."""
    classes = {}
    for name, nodes in nets_with_meta.items():
        fns = {(n[2] or "").upper() for n in nodes if n[2]}
        has_power_in = any("power_in" in _pintypes(n) for n in nodes)
        if _matches(fns, GROUND_FUNCTION_TOKENS):
            classes[name] = "GND"
        elif _matches(fns, ANALOG_FUNCTION_TOKENS):
            classes[name] = "ANALOG"
        elif _matches(fns, POWER_FUNCTION_TOKENS) or has_power_in:
            classes[name] = "POWER"
        else:
            classes[name] = "SIGNAL"
    return classes


# ------------------------------------------------------------ resolution
def resolve_class_rules(class_name, fab=FAB_PROFILE_PCBPOWER,
                        current_a=None, external=True):
    """Return (rules, provenance) for one net class."""
    prov = {}
    if current_a is None:
        current_a = CLASS_DEFAULT_CURRENT_A[class_name]
        cur_src = "default-unverified"
    else:
        cur_src = "supplied"

    t2_track = ipc2221_width_mm(current_a, external=external)
    t1_track = fab["min_track_mm"]
    track = max(t1_track, t2_track, PRACTICAL_MIN_TRACK_MM)
    if track == t2_track:
        prov["track_mm"] = "tier2-ipc2221(I=%.3fA,%s)" % (current_a, cur_src)
    elif track == PRACTICAL_MIN_TRACK_MM:
        prov["track_mm"] = "policy-practical-min(margin over fab floor)"
    else:
        prov["track_mm"] = "tier1-fab(%s)" % fab["name"]

    t1_clear = fab["min_clearance_mm"]
    t3_clear = CLASS_MIN_CLEARANCE_MM[class_name]
    clearance = max(t1_clear, t3_clear)
    prov["clearance_mm"] = ("tier3-class-policy" if t3_clear > t1_clear
                            else "tier1-fab(%s)" % fab["name"])

    drill = fab["min_drill_mm"]
    via = drill + 2 * fab["min_annular_ring_mm"]
    prov["via_drill_mm"] = "tier1-fab(%s)" % fab["name"]
    prov["via_dia_mm"] = "tier1-fab drill + 2*annular(UNVERIFIED annular)"

    rules = {
        "track_mm": round(track, 3),
        "clearance_mm": round(clearance, 3),
        "via_drill_mm": round(drill, 3),
        "via_dia_mm": round(via, 3),
    }
    return rules, prov


def build_rule_table(nets_with_meta, fab=FAB_PROFILE_PCBPOWER,
                     currents=None, external=True):
    """Returns (net_class_map, class_rules, provenance)."""
    currents = currents or {}
    net_class = classify_nets(nets_with_meta)
    used = sorted(set(net_class.values()))
    class_rules, prov = {}, {}
    for c in used:
        # if any net in this class has a supplied current, use the max
        cur = max((currents[n] for n, cc in net_class.items()
                   if cc == c and n in currents), default=None)
        class_rules[c], prov[c] = resolve_class_rules(c, fab, cur, external)
    return net_class, class_rules, prov



def plane_candidates(net_class, nets_with_meta):
    """Which nets should become copper planes, DERIVED not hardcoded.
    Ground plane = the GND-class net with the most nodes.
    Power plane  = the POWER-class net with the most nodes (the main rail).
    Returns (ground_net, power_net); either may be None on odd designs."""
    def biggest(cls):
        cands = [n for n, c in net_class.items() if c == cls]
        if not cands:
            return None
        return max(cands, key=lambda n: len(nets_with_meta.get(n, ())))
    return biggest("GND"), biggest("POWER")
