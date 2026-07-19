"""Stage-5 runner: build the decap assignment and verify it against known truth."""
from netlist_reader import parse_netlist_nets, resolve_path
from grouping import parse_netlist_values, assign_decaps

NET = "C:\\Users\\Dushyant\\Desktop\\pcbgen_outputs\\stage4\\stage4.net"

NET = resolve_path(NET)
nets = parse_netlist_nets(NET)
values = parse_netlist_values(NET)
asg = assign_decaps(nets, values)

fails = []
for rail in sorted(asg):
    a = asg[rail]
    print(rail, "| pairs:", [(p, c) for p, c in a["pairs"]],
          "| bulk:", a["bulk"], "| spare:", a["spare_caps"],
          "| unpaired:", a["unpaired_pads"])
    if a["spare_caps"] or a["unpaired_pads"]:
        fails.append(rail)

v33 = asg.get("/VDD_3V3", {})
v12 = asg.get("/VDD12", {})
ok = (len(v33.get("pairs", [])) == 5
      and v12.get("policy") == "per_rail" and not v12.get("unpaired_pads")
      and sorted(v33.get("bulk", [])) == ["C11", "C14", "C9"]
      and not fails)
print("STAGE5 SELFCHECK", "PASS" if ok else "FAIL", 
      "" if not fails else ("(imbalanced rails: %s)" % fails))
