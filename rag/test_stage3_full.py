#!/usr/bin/env python3
"""
Stage 3a: FULL power structure for U1.
  - 5 single-pin rails (VREF_PLUS, VBAT, VDDA, VDDIO2, VDDUSB) -> WIRED as
    ST-style T-junctions (the Stage-2-proven geometry).
  - VDD_3V3 (3 pins) and VDD12 (2 pins) -> too crowded to wire cleanly ->
    LABELED at the pins, with their caps in a tidy supply region below the IC
    (rail label on top pin, GND symbol below).
Routability rule: wire a rail if its stacks fit the free space between
neighbouring rails' pins; otherwise label it.
"""
import os
from skidl import *
lib_search_paths[KICAD].append(os.environ.get("KICAD_SYMBOL_DIR",
    "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols"))
import netlist_parser, component_model, placement
from kicad_sch_builder import SchematicBuilder

GRID = 1.27; PITCH = 7.62; CAP_OFF = 6.35
def snap(v): return round(round(v / GRID) * GRID, 2)

src = open("lsm6dsm_stm32l476_spi_v2.py").read()
src = src.replace("from skidl import *", "").replace("ERC()", "")
src = "\n".join(l for l in src.split("\n") if "lib_search_paths" not in l)
exec(src)
comps = component_model.build_components(netlist_parser.parse_circuit(default_circuit))
pl = placement.place_components(comps)
u1x, u1y = pl["U1"]

b = SchematicBuilder("Stage3 power structure", "test", project_name="stage3")
b.add_ic_by_name("U1", "STM32L476JGYxP", u1x, u1y)

# ---------- WIRED rails (proven Stage 2 T-junction) ----------
WIRED = {"VREF_PLUS": ("G8", "10nF"), "VBAT": ("B9", "100nF"),
         "VDDA": ("H9", "10nF"), "VDDIO2": ("B6", "100nF"),
         "VDDUSB": ("A1", "1uF")}
rails = []
for rail, (pin, cval) in WIRED.items():
    ex, ey = b.pin_endpoint("U1", pin)
    rails.append([ex, ey, rail, pin, cval])
rails.sort()
prev = None
for r in rails:
    r.append(snap(r[0]) if prev is None else snap(max(r[0], prev + PITCH)))
    prev = r[-1]
# safety: no cap-x may land on another stack's junction-x (Stage 2 lesson)
jx = {r[5] for r in rails}
for r in rails:
    assert snap(r[5] - CAP_OFF) not in jx, f"{r[2]} cap collides with a junction"

def t_junction(pin_x, pin_y, stack_x, rail, cval, step_idx=0):
    stepped = abs(stack_x - pin_x) > 0.01
    step_y = snap(pin_y - 5.08 + step_idx * 2.54)   # own jog track per stepped rail
    jy   = snap(pin_y - 19.05)
    pwry = snap(pin_y - 24.13)
    if stepped:
        b.add_wire(pin_x, pin_y, pin_x, step_y)
        b.add_wire(pin_x, step_y, stack_x, step_y)
        b.add_wire(stack_x, step_y, stack_x, jy)
    else:
        b.add_wire(pin_x, pin_y, stack_x, jy)
    b.add_wire(stack_x, jy, stack_x, pwry)
    b.add_junction(stack_x, jy)
    b.add_label(rail, stack_x, snap(jy - 2.54))       # names the rail net
    capx = snap(stack_x - CAP_OFF)
    cref, ctop, cbot = b.add_capacitor(cval, capx, snap(jy + 3.81), rot=0)
    b.add_wire(ctop[0], ctop[1], stack_x, jy)          # cap taps the junction
    b.add_power(rail, stack_x, pwry)
    gy = snap(cbot[1] + 2.54)
    b.add_wire(cbot[0], cbot[1], cbot[0], gy)
    b.add_power("GND", cbot[0], gy)

si = 0
for pin_x, pin_y, rail, pin, cval, stack_x in rails:
    stepped = abs(stack_x - pin_x) > 0.01
    t_junction(pin_x, pin_y, stack_x, rail, cval, si if stepped else 0)
    if stepped: si += 1
    b.ics["U1"]["used_pins"].add(pin)
    print(f"WIRED   {rail:<10} pin={pin} stack_x={stack_x:.2f}")

# ---------- LABELED rails: net-label at each pin ----------
LABELED = {"VDD_3V3": ["A9", "F1", "H8"], "VDD12": ["B8", "J1"]}
for rail, pins in LABELED.items():
    for pin in pins:
        ex, ey = b.pin_endpoint("U1", pin)
        stub_end = snap(ey - 3.81)                      # stub endpoint
        b.add_wire(ex, ey, ex, stub_end)               # stub up from the pin
        b.add_label(rail, ex, stub_end)                # label ON the endpoint
        b.ics["U1"]["used_pins"].add(pin)
    print(f"LABELED {rail:<10} pins={pins}")

# ---------- supply region below the IC for the labeled rails' caps ----------
REGION = [("VDD_3V3","100nF"),("VDD_3V3","100nF"),("VDD_3V3","100nF"),
          ("VDD_3V3","4.7uF"),("VDD_3V3","100nF"),("VDD_3V3","10uF"),
          ("VDD_3V3","100nF"),("VDD_3V3","10uF"),
          ("VDD12","1uF"),("VDD12","100nF")]
driven_brails = set()
IC_BOT = snap(u1y + 48.26)
SX, SY = snap(16.51), snap(IC_BOT + 20.32)
COLP, ROWP, PER = 15.24, 25.40, 6
for i, (rail, val) in enumerate(REGION):
    cx = snap(SX + (i % PER) * COLP)
    cy = snap(SY + (i // PER) * ROWP)
    cref, ctop, cbot = b.add_capacitor(val, cx, cy, rot=0)
    lab_y = snap(ctop[1] - 3.81)                    # stub endpoint
    b.add_wire(ctop[0], ctop[1], ctop[0], lab_y)   # stub up from cap top pin
    b.add_label(rail, ctop[0], lab_y)              # label ON the endpoint
    # ONE power driver per B-rail net: add_power's power_nets_used set makes
    # this a no-op after the first call, so exactly one PWR_FLAG per rail
    # (two would recreate the Stage-2 pin_to_pin power-output short).
    if rail not in driven_brails:
        b.add_power(rail, ctop[0], lab_y)
        driven_brails.add(rail)
    gy = snap(cbot[1] + 2.54)
    b.add_wire(cbot[0], cbot[1], cbot[0], gy)
    b.add_power("GND", cbot[0], gy)
print(f"supply region: {len(REGION)} caps below IC at y>={SY}")

out = "/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs/stage3"
os.makedirs(out, exist_ok=True)
p = os.path.join(out, "stage3.kicad_sch")
open(p, "w").write(b.build())
print(f"\nsaved: {p}")
