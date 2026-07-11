#!/usr/bin/env python3
"""Stage 2b (fixed): ALL 5 A-rails. Cap offset 6.35 (!= 7.62 stack spacing)
so cap-tap wires don't land on neighbouring junctions -> no rail merge."""
import os
from skidl import *
lib_search_paths[KICAD].append(os.environ.get("KICAD_SYMBOL_DIR",
    "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols"))
import netlist_parser, component_model, placement
from kicad_sch_builder import SchematicBuilder

GRID = 1.27; MIN_CLEAR = 7.62; CAP_OFFSET = 6.35
def snap(v): return round(round(v / GRID) * GRID, 2)

src = open("lsm6dsm_stm32l476_spi_v2.py").read()
src = src.replace("from skidl import *", "").replace("ERC()", "")
src = "\n".join(l for l in src.split("\n") if "lib_search_paths" not in l)
exec(src)
comps = component_model.build_components(netlist_parser.parse_circuit(default_circuit))
pl = placement.place_components(comps)
u1x, u1y = pl["U1"]

b = SchematicBuilder("All A-rails test", "test", project_name="arails_test")
b.add_ic_by_name("U1", "STM32L476JGYxP", u1x, u1y)

A_RAILS = {
    "VREF_PLUS": ("G8", "1uF"), "VBAT": ("B9", "100nF"), "VDDA": ("H9", "1uF"),
    "VDDIO2": ("B6", "100nF"), "VDDUSB": ("A1", "1uF"),
}
rails = []
for rail, (pin, cval) in A_RAILS.items():
    ex, ey = b.pin_endpoint("U1", pin)
    rails.append([ex, ey, rail, pin, cval])
rails.sort()
prev = None
for r in rails:
    r.append(snap(r[0]) if prev is None else snap(max(r[0], prev + MIN_CLEAR)))
    prev = r[-1]

# safety: assert no cap-x lands on any junction-x (would re-merge)
junction_xs = {r[5] for r in rails}
for r in rails:
    capx = snap(r[5] - CAP_OFFSET)
    assert capx not in junction_xs, f"{r[2]} cap_x={capx} lands on a junction! merge risk"

def build_tjunction(pin_x, pin_y, stack_x, rail, cval):
    stepped = abs(stack_x - pin_x) > 0.01
    step_up_y = snap(pin_y - 5.08)
    jy = snap(pin_y - 19.05)
    pwry = snap(pin_y - 24.13)
    if stepped:
        b.add_wire(pin_x, pin_y, pin_x, step_up_y)
        b.add_wire(pin_x, step_up_y, stack_x, step_up_y)
        b.add_wire(stack_x, step_up_y, stack_x, jy)
    else:
        b.add_wire(pin_x, pin_y, stack_x, jy)
    b.add_wire(stack_x, jy, stack_x, pwry)
    b.add_junction(stack_x, jy)
    # NAME the rail net: without a label, ST-specific rails are anonymous power
    # nets and KiCad merges their PWR_FLAGs (pin_to_pin power-output short).
    b.add_label(rail, stack_x, snap(jy - 2.54))
    capx = snap(stack_x - CAP_OFFSET)
    capy = snap(jy + 3.81)
    cref, ctop, cbot = b.add_capacitor(cval, capx, capy, rot=0)
    b.add_wire(ctop[0], ctop[1], stack_x, jy)      # cap tap
    b.add_power(rail, stack_x, pwry)
    gnd_y = snap(cbot[1] + 2.54)
    b.add_wire(cbot[0], cbot[1], cbot[0], gnd_y)
    b.add_power("GND", cbot[0], gnd_y)

for pin_x, pin_y, rail, pin, cval, stack_x in rails:
    build_tjunction(pin_x, pin_y, stack_x, rail, cval)
    if "U1" in b.ics and "used_pins" in b.ics["U1"]:
        b.ics["U1"]["used_pins"].add(pin)
    print(f"{rail:<10} pin={pin} stack_x={stack_x:.2f} cap_x={snap(stack_x-CAP_OFFSET):.2f} cap={cval}")

out = "/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs/arails_test"
os.makedirs(out, exist_ok=True)
path = os.path.join(out, "arails_test.kicad_sch")
open(path, "w").write(b.build())
print(f"\nsaved: {path}")
