"""
component_model.py -- Module 4, Stage 2: component model.
Enriches the Stage-1 connectivity model with resolved symbols + pin geometry
+ per-pin net mapping. Count- and type-agnostic (IC or passive, same path).
"""

import os
from kiutils.symbol import SymbolLib
from kicad_symbol_parser import KicadSymbol

SYMDIR = os.environ.get("KICAD_SYMBOL_DIR",
    "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols")

_PASSIVE_NAMES = {"R", "C", "L"}


def _load_symbol_direct(library, name):
    if not library:
        return None
    path = os.path.join(SYMDIR, library + ".kicad_sym")
    if not os.path.isfile(path):
        return None
    lib = SymbolLib.from_file(path)
    matches = [s for s in lib.symbols if s.entryName == name]
    if not matches:
        return None
    return KicadSymbol.from_kiutils(matches[0], library, lib_path=path)


def _classify(part_info):
    if part_info["name"] in _PASSIVE_NAMES and len(part_info["pins"]) == 2:
        return "passive"
    return "ic"


def build_components(model):
    pin_net = model["pin_net"]
    components = {}
    unresolved = []

    for ref, info in model["parts"].items():
        sym = _load_symbol_direct(info["library"], info["name"])
        if sym is None:
            unresolved.append((ref, info["library"], info["name"]))
            continue
        pins = {}
        for p in sym.pins:
            num = str(p["number"])
            pins[num] = {
                "net": pin_net.get((ref, num)),
                "x": p["x"], "y": p["y"], "angle": p["angle"],
                "length": p["length"], "type": p["type"],
                "name": p["name"], "hidden": p["hidden"],
            }
        components[ref] = {
            "name": info["name"], "library": info["library"],
            "value": info["value"], "kind": _classify(info),
            "footprint": info.get("footprint"),
            "symbol": sym, "pins": pins,
        }

    if unresolved:
        raise KeyError("Stage 2 could not resolve symbols for: "
            + ", ".join(f"{r}({lib}:{nm})" for r, lib, nm in unresolved))
    return components


def summarize_components(components):
    from collections import Counter
    kinds = Counter(c["kind"] for c in components.values())
    lines = [f"Components: {len(components)}  ({dict(kinds)})"]
    net_pins = nc_pins = 0
    for c in components.values():
        for pd in c["pins"].values():
            if pd["net"]:
                net_pins += 1
            else:
                nc_pins += 1
    lines.append(f"Pins on a net: {net_pins}   Pins with no net (NC/unused): {nc_pins}")
    return "\n".join(lines)
