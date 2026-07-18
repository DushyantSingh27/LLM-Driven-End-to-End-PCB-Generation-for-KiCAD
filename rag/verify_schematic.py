#!/usr/bin/env python3
"""
verify_schematic.py -- verify a generated .kicad_sch against its netlist spec.

KiCad ERC checks pin-type rules; it has NO concept of design intent, so it
cannot detect (a) two power rails silently merged, or (b) a signal pin landing
on a power net. Both are silent, shippable faults -- we hit both.

Principle: the netlist says what SHOULD connect; the schematic says what DOES.
    for every pin: net(drawn) must equal net(netlist)
  - a drawn net carrying two rail names      -> RAIL MERGE
  - a pin drawn on a net the netlist denies  -> SHORT
  - a pin in the netlist but on no drawn net -> MISSING
"""
import re
from collections import defaultdict


def _r(v): return round(float(v), 2)


class _UnionFind:
    def __init__(self): self.parent = {}
    def find(self, p):
        self.parent.setdefault(p, p)
        root = p
        while self.parent[root] != root: root = self.parent[root]
        while self.parent[p] != root: self.parent[p], p = root, self.parent[p]
        return root
    def union(self, a, b): self.parent[self.find(a)] = self.find(b)
    def has(self, p): return p in self.parent


class Report:
    def __init__(self):
        self.rail_merges = []
        self.shorts = []
        self.missing = []
        self.dangling_labels = []
    def ok(self):
        return not (self.rail_merges or self.shorts or self.missing
                    or self.dangling_labels)
    def __str__(self):
        if self.ok():
            return "VERIFY: PASS -- drawing implements the netlist exactly."
        out = ["VERIFY: FAIL"]
        for a, b in self.rail_merges:
            out.append(f"  RAIL MERGE: '{a}' + '{b}' drawn on one net; netlist says separate")
        for ref, pin, drawn, spec in self.shorts:
            out.append(f"  SHORT: {ref}.{pin} drawn on '{drawn}', netlist says '{spec}'")
        for ref, pin, spec in self.missing:
            out.append(f"  MISSING: {ref}.{pin} should be on '{spec}', not connected")
        for name, x, y in self.dangling_labels:
            out.append(f"  DANGLING LABEL: '{name}' at ({x},{y}) lies on no wire")
        return "\n".join(out)


def _parse_wires(txt):
    return [(_r(a), _r(b), _r(c), _r(d)) for a, b, c, d in re.findall(
        r'\(wire \(pts \(xy ([-\d.]+) ([-\d.]+)\) \(xy ([-\d.]+) ([-\d.]+)\)\)', txt)]

def _parse_labels(txt):
    return [(n, _r(x), _r(y)) for n, x, y in re.findall(
        r'\(label "([^"]+)" \(at ([-\d.]+) ([-\d.]+)', txt)]

def _parse_power_syms(txt):
    out = []
    for lib, x, y in re.findall(
            r'\(symbol \(lib_id "power:([^"]+)"\) \(at ([-\d.]+) ([-\d.]+)', txt):
        if lib != "PWR_FLAG":
            out.append((lib, _r(x), _r(y)))
    return out

def _on_wire(px, py, wires):
    for x1, y1, x2, y2 in wires:
        if abs(x1-x2) < 0.01 and abs(px-x1) < 0.01:
            if min(y1,y2)-0.01 <= py <= max(y1,y2)+0.01: return True
        if abs(y1-y2) < 0.01 and abs(py-y1) < 0.01:
            if min(x1,x2)-0.01 <= px <= max(x1,x2)+0.01: return True
    return False

def _component_at(uf, wires, px, py):
    if uf.has((px, py)): return uf.find((px, py))
    for x1, y1, x2, y2 in wires:
        if abs(x1-x2) < 0.01 and abs(px-x1) < 0.01:
            if min(y1,y2)-0.01 <= py <= max(y1,y2)+0.01: return uf.find((x1,y1))
        if abs(y1-y2) < 0.01 and abs(py-y1) < 0.01:
            if min(x1,x2)-0.01 <= px <= max(x1,x2)+0.01: return uf.find((x1,y1))
    return None


def verify(sch_path, components, placement):
    """Compare drawn connectivity against the netlist spec.

    Connection model (matches how KiCad forms nets):
      * wires connect their two endpoints;
      * a label or power symbol AT a point names the net at that point --
        whether the point is on a wire OR on a bare pin;
      * two pins at the SAME coordinate are the same node (stacked power pins,
        and any co-located pins).
    A net is a connected group of anchors; a pin belongs to the group its
    coordinate falls in.
    """
    txt = open(sch_path).read()
    wires = _parse_wires(txt)
    rep = Report()

    uf = _UnionFind()
    for x1, y1, x2, y2 in wires:
        uf.union((x1, y1), (x2, y2))

    # every pin coordinate is an anchor; co-located pins union together
    pin_at = defaultdict(list)                 # coord -> [(ref, num)]
    for ref, comp in components.items():
        if ref not in placement:
            continue
        icx, icy = placement[ref]
        for num, pd in comp["pins"].items():
            if pd.get("hidden"):
                continue
            p = (_r(icx + pd["x"]), _r(icy - pd["y"]))
            uf.union(p, p)                     # ensure the node exists
            pin_at[p].append((ref, num))
    # a pin that lies mid-wire joins that wire's component
    for p in list(pin_at):
        c = _component_at(uf, wires, *p)
        if c is not None:
            uf.union(p, c)

    # labels + power symbols name the net at their point (wire OR bare pin)
    comp_names = defaultdict(set)
    def _anchor(x, y):
        if uf.has((x, y)):
            return uf.find((x, y))
        return _component_at(uf, wires, x, y)   # snaps onto a wire if mid-span
    for name, x, y in _parse_labels(txt):
        c = _anchor(x, y)
        if c is None:
            rep.dangling_labels.append((name, x, y))
        else:
            comp_names[c].add(name)
    for name, x, y in _parse_power_syms(txt):
        c = _anchor(x, y)
        if c is None:
            for dy in (1.27, -1.27, 2.54, -2.54, 3.81, -3.81):
                c = _anchor(x, _r(y + dy))
                if c is not None:
                    break
        if c is not None:
            comp_names[c].add(name)

    # RAIL MERGE: one net carrying two different power-rail names.
    # (Signal nets legitimately have one name; a power rail + its own name is
    # fine; two DIFFERENT names on one net is the fault.)
    for c, names in comp_names.items():
        names = sorted(names)
        if len(names) > 1:
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    rep.rail_merges.append((names[i], names[j]))

    # every pin: drawn net must equal the netlist's net
    for ref, comp in components.items():
        if ref not in placement:
            continue
        icx, icy = placement[ref]
        for num, pd in comp["pins"].items():
            if pd.get("hidden"):
                continue
            spec = pd.get("net")
            p = (_r(icx + pd["x"]), _r(icy - pd["y"]))
            c = uf.find(p) if uf.has(p) else None
            drawn = comp_names.get(c, set()) if c is not None else set()
            if spec is None:
                for d in drawn:
                    rep.shorts.append((ref, num, d, "None (should float)"))
            elif not drawn:
                rep.missing.append((ref, num, spec))
            elif spec not in drawn:
                for d in drawn:
                    rep.shorts.append((ref, num, d, spec))
    return rep
