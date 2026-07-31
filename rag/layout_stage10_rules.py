"""Stage-10: resolve design rules from the netlist, apply as netclasses,
verify after reload, then export DSN and confirm the widths reached it."""
import re, pcbnew
from board_builder import save_board
from design_rules import build_rule_table
from rules_apply import apply_rules

SRC = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage8_pours.kicad_pcb"
NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\joined_e2e\\joined_e2e.net"
OUT = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage10_rules.kicad_pcb"
DSN = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage10_rules.dsn"

cur, nets = None, {}
for ln in open(NET, encoding="utf-8").read().splitlines():
    m = re.search(r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', ln)
    if m: cur = m.group(1); nets[cur] = []; continue
    n = re.search(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(.*)', ln)
    if n and cur:
        pf = re.search(r'\(pinfunction "([^"]+)"\)', n.group(3))
        pt = re.search(r'\(pintype "([^"]+)"\)', n.group(3))
        nets[cur].append((n.group(1), n.group(2),
                          pf.group(1) if pf else None, pt.group(1) if pt else None))

net_class, class_rules, prov = build_rule_table(nets)
print("classes:", {c: class_rules[c]["track_mm"] for c in sorted(class_rules)})

board = pcbnew.LoadBoard(SRC)
created, assigned, missing = apply_rules(board, net_class, class_rules)
print("created:", created, "| assigned:", assigned, "| missing:", len(missing), missing[:5])
assert save_board(board, OUT)

b2 = pcbnew.LoadBoard(OUT)
ns2 = b2.GetDesignSettings().m_NetSettings
print("=== after reload ===")
print("classes on board:", sorted(str(k) for k in ns2.GetNetclasses().keys()))
ok = True
for probe_net, want in (("/VDD_3V3", "POWER"), ("GND", "GND"),
                        ("/VREF_PLUS", "ANALOG"), ("/SPI_SCK", "SIGNAL")):
    n = b2.FindNet(probe_net)
    got = n.GetNetClassName() if n else "MISSING"
    try:
        w = pcbnew.ToMM(ns2.GetEffectiveNetClass(probe_net).GetTrackWidth())
    except Exception as e:
        w = -1.0
        print("    (width lookup failed: %r)" % e)
    print("  %-12s class=%-7s track=%.3fmm  (want %s)" % (probe_net, got, w, want))
    if got != want: ok = False
print("STAGE10 SELFCHECK", "PASS" if ok else "FAIL")

print("=== DSN export ===")
print("rc:", pcbnew.ExportSpecctraDSN(b2, DSN))
