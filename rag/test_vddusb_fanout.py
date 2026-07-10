#!/usr/bin/env python3
"""Stage 2a: ONE fanned-out A-rail (VDDUSB) with a stepped wire into free space.
Proves the stepped-wire topology connects before scaling to all 5 A-rails."""
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

b = SchematicBuilder("VDDUSB fanout test", "test", project_name="vddusb_test")
b.add_ic_by_name("U1", "STM32L476JGYxP", u1x, u1y)

px, py = b.pin_endpoint("U1", "A1")   # VDDUSB
print(f"VDDUSB pin endpoint: ({px:.2f}, {py:.2f})")

# fanned stack, raised so cap+GND clear the horizontal step wire
stack_x = snap(px + 10.16)            # stack 8 grid right of pin
step_up_y = snap(py - 5.08)           # rise then jog across at this y
jy = snap(py - 19.05)                 # junction (raised: 15 grid above pin)
pwry = snap(py - 24.13)
capx = snap(stack_x - 7.62)
cap_top_y = jy
capy = snap(cap_top_y + 3.81)

# stepped wire: pin -> up -> across -> up to junction
b.add_wire(px, py, px, step_up_y)              # seg1 pin up
b.add_wire(px, step_up_y, stack_x, step_up_y)  # seg2 across
b.add_wire(stack_x, step_up_y, stack_x, jy)    # seg3 up to junction
b.add_wire(stack_x, jy, stack_x, pwry)         # junction -> power
b.add_junction(stack_x, jy)
cref, cpin_top, cpin_bot = b.add_capacitor("1uF", capx, capy, rot=0)
print(f"cap {cref}: top={cpin_top} bot={cpin_bot}")
b.add_wire(cpin_top[0], cpin_top[1], stack_x, jy)   # cap top -> junction (tap)
b.add_power("VDDUSB", stack_x, pwry)
gnd_y = snap(cpin_bot[1] + 2.54)
b.add_wire(cpin_bot[0], cpin_bot[1], cpin_bot[0], gnd_y)
b.add_power("GND", cpin_bot[0], gnd_y)

if "U1" in b.ics and "used_pins" in b.ics["U1"]:
    b.ics["U1"]["used_pins"].add("A1")

out = "/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs/vddusb_test"
os.makedirs(out, exist_ok=True)
path = os.path.join(out, "vddusb_test.kicad_sch")
open(path, "w").write(b.build())
print(f"\nsaved: {path}")
