#!/usr/bin/env python3
"""Standalone test of ONE atomic T-junction (VBAT) -- cap lifted clear of IC."""
import os
from skidl import *
lib_search_paths[KICAD].append(os.environ.get("KICAD_SYMBOL_DIR",
    "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols"))
import netlist_parser, component_model, placement
from kicad_sch_builder import SchematicBuilder

GRID = 1.27
def snap(v): return round(round(v / GRID) * GRID, 2)

src = open("lsm6dsm_stm32l476_spi_v2.py").read()
src = src.replace("from skidl import *", "").replace("ERC()", "")
src = "\n".join(l for l in src.split("\n") if "lib_search_paths" not in l)
exec(src)
comps = component_model.build_components(netlist_parser.parse_circuit(default_circuit))
pl = placement.place_components(comps)
u1x, u1y = pl["U1"]

b = SchematicBuilder("VBAT T-junction test", "test", project_name="vbat_test")
b.add_ic_by_name("U1", "STM32L476JGYxP", u1x, u1y)

px, py = b.pin_endpoint("U1", "B9")
print(f"VBAT pin endpoint: ({px:.2f}, {py:.2f})")

# T-junction geometry, cap fully above the pin tip (clears IC):
jx, jy = px, snap(py - 15.24)        # junction 12 grid above pin
pwrx, pwry = px, snap(py - 20.32)    # power source above junction
capx = snap(px - 7.62)               # cap 6 grid left
cap_top_y = jy                       # cap top pin taps junction height
capy = snap(cap_top_y + 3.81)        # cap center below its top pin
cap_bot_y = snap(capy + 3.81)

b.add_wire(px, py, jx, jy)                       # pin -> junction
b.add_wire(jx, jy, pwrx, pwry)                   # junction -> power source
b.add_junction(jx, jy)                           # junction dot
cref, cpin_top, cpin_bot = b.add_capacitor("100nF", capx, capy, rot=0)
print(f"cap {cref}: top={cpin_top} bot={cpin_bot}")
b.add_wire(cpin_top[0], cpin_top[1], jx, jy)     # cap top -> junction (tap)
b.add_power("VBAT", pwrx, pwry)                   # VBAT source (label+PWR_FLAG)
gnd_y = snap(cpin_bot[1] + 2.54)
b.add_wire(cpin_bot[0], cpin_bot[1], cpin_bot[0], gnd_y)  # cap bot -> GND stub
b.add_power("GND", cpin_bot[0], gnd_y)            # GND symbol

if "U1" in b.ics and "used_pins" in b.ics["U1"]:
    b.ics["U1"]["used_pins"].add("B9")

out = "/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs/vbat_test"
os.makedirs(out, exist_ok=True)
path = os.path.join(out, "vbat_test.kicad_sch")
open(path, "w").write(b.build())
print(f"\nsaved: {path}")
