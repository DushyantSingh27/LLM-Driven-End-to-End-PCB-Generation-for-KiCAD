"""Which nets got routed, and how much - read from the SES itself."""
import re, sys, collections
ses = open(sys.argv[1], encoding="utf-8", errors="replace").read()
wires = collections.Counter()
for m in re.finditer(r'\(wire\s*\(path\s+(\S+)', ses):
    wires["layer:" + m.group(1)] += 1
nets = re.findall(r'\(net\s+(\S+)', ses)
print("nets appearing in SES:", len(set(nets)))
print("wire segments per layer:", dict(wires))
vias = len(re.findall(r'\(via\s', ses))
print("vias:", vias)
print("=== per-net wire counts ===")
per = collections.Counter()
for m in re.finditer(r'\(net\s+(\S+)(.*?)(?=\(net\s+|\Z)', ses, re.S):
    per[m.group(1)] = len(re.findall(r'\(wire\s', m.group(2)))
for n, c in sorted(per.items(), key=lambda x: -x[1]):
    print("   %-32s %d" % (n, c))
