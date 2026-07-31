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


def parse_netlist_nets_meta(net_path):
    """{netname: [(ref, pin, pinfunction, pintype), ...]} - carries the pin
    semantics the design-rules resolver classifies on. Regex verified against
    the real netlist. parse_netlist_nets() is left alone for its callers."""
    import re
    cur, nets = None, {}
    for ln in open(net_path, "r", encoding="utf-8").read().splitlines():
        m = re.search(r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', ln)
        if m:
            cur = m.group(1)
            nets[cur] = []
            continue
        n = re.search(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(.*)', ln)
        if n and cur is not None:
            rest = n.group(3)
            pf = re.search(r'\(pinfunction "([^"]+)"\)', rest)
            pt = re.search(r'\(pintype "([^"]+)"\)', rest)
            nets[cur].append((n.group(1), n.group(2),
                              pf.group(1) if pf else None,
                              pt.group(1) if pt else None))
    return nets
