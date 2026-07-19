"""netlist_reader.py - pure-text kicadsexpr netlist parsing (no pcbnew).
Importable under any Python: WSL venv or KiCad bundled python.exe."""

def parse_netlist_components(net_path):
    """Parse (ref, lib, footprint_name) triples from a kicadsexpr netlist.
    Relies on verified structure: '(footprint "Lib:Name")' is the line
    immediately after '(comp (ref "X")'. Fails loudly on any deviation."""
    import re
    comps = []
    lines = open(net_path, "r", encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        m = re.search(r'\(comp \(ref "([^"]+)"\)', lines[i])
        if m:
            ref = m.group(1)
            # scan forward inside this comp block until footprint or next comp
            full = None
            j = i + 1
            while j < len(lines) and '(comp (ref' not in lines[j]:
                fm = re.search(r'\(footprint "([^"]+)"\)', lines[j])
                if fm:
                    full = fm.group(1)
                    break
                j += 1
            if full is None:
                raise RuntimeError("comp %s: no footprint before next comp" % ref)
            if ":" not in full:
                raise RuntimeError("comp %s: footprint %r has no Lib: prefix" % (ref, full))
            lib, name = full.split(":", 1)
            comps.append((ref, lib + ".pretty", name))
        i += 1
    return comps



def parse_netlist_nets(net_path):
    """Parse [(netname, [(ref, pin), ...]), ...] from a kicadsexpr netlist.
    Keys only on quoted fields; net headers and nodes are one per line
    (verified structure). Fails loudly on a node outside any net."""
    import re
    nets = []
    current = None
    for ln in open(net_path, "r", encoding="utf-8").read().splitlines():
        nm = re.search(r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', ln)
        if nm:
            current = (nm.group(1), [])
            nets.append(current)
            continue
        nd = re.search(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', ln)
        if nd:
            if current is None:
                raise RuntimeError("node line outside any net: %r" % ln)
            current[1].append((nd.group(1), nd.group(2)))
    return nets




def resolve_path(win_path):
    """Return the correct form of a C:\\... path for the current interpreter.
    Windows python.exe -> unchanged; WSL/Linux -> /mnt/c/... form."""
    import sys
    if sys.platform == "win32":
        return win_path
    p = win_path.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = "/mnt/" + p[0].lower() + p[2:]
    return p
