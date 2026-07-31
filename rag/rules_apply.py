"""rules_apply.py - applies the resolver's rule table to a board (pcbnew-bound).

Knows nothing about WHY a width is what it is; design_rules.py owns that.
Verified 9.0 API (probe: probe_netclass_assign.py):
  pcbnew.NETCLASS(name)                  - construct
  nc.SetTrackWidth/SetClearance/SetViaDiameter/SetViaDrill
  ns.SetNetclass(name, nc)               - INSERT (note: netclasses_map[name]=nc
                                           fails SILENTLY - do not use)
  net.SetNetClass(nc)                    - per-net assignment
  ns.RecomputeEffectiveNetclasses()      - commit
All verified to survive save->reload with correct effective track width.
"""
import pcbnew


def _make_netclass(name, rules):
    nc = pcbnew.NETCLASS(name)
    nc.SetTrackWidth(pcbnew.FromMM(rules["track_mm"]))
    nc.SetClearance(pcbnew.FromMM(rules["clearance_mm"]))
    nc.SetViaDiameter(pcbnew.FromMM(rules["via_dia_mm"]))
    nc.SetViaDrill(pcbnew.FromMM(rules["via_drill_mm"]))
    return nc


def apply_rules(board, net_class, class_rules, default_class="SIGNAL"):
    """Create a netclass per class, assign every net, update Default.
    net_class:   {netname: class_name}   (from design_rules.build_rule_table)
    class_rules: {class_name: {track_mm, clearance_mm, via_dia_mm, via_drill_mm}}
    Returns (created, assigned, missing) - missing = nets not found on board."""
    ns = board.GetDesignSettings().m_NetSettings

    made = {}
    for cname, rules in sorted(class_rules.items()):
        nc = _make_netclass(cname, rules)
        ns.SetNetclass(cname, nc)
        if not ns.HasNetclass(cname):
            raise RuntimeError("netclass %r did not register" % cname)
        made[cname] = nc

    # Default carries the signal rules so any unassigned net is still sane
    if default_class in class_rules:
        d = ns.GetDefaultNetclass()
        r = class_rules[default_class]
        d.SetTrackWidth(pcbnew.FromMM(r["track_mm"]))
        d.SetClearance(pcbnew.FromMM(r["clearance_mm"]))
        d.SetViaDiameter(pcbnew.FromMM(r["via_dia_mm"]))
        d.SetViaDrill(pcbnew.FromMM(r["via_drill_mm"]))

    assigned, missing = 0, []
    for netname, cname in net_class.items():
        net = board.FindNet(netname)
        if net is None:
            missing.append(netname)
            continue
        # Pattern assignment is what PERSISTS in the board file; net.SetNetClass
        # is runtime-only and is recomputed from patterns on load (verified:
        # net.SetNetClass alone -> every net reads back as "Default").
        ns.SetNetclassPatternAssignment(netname, cname)
        # Pattern assignment is what PERSISTS in the board file; net.SetNetClass
        # is runtime-only and is recomputed from patterns on load (verified:
        # net.SetNetClass alone -> every net reads back as "Default").
        ns.SetNetclassPatternAssignment(netname, cname)
        net.SetNetClass(made[cname])
        assigned += 1

    ns.RecomputeEffectiveNetclasses()
    return len(made), assigned, missing
