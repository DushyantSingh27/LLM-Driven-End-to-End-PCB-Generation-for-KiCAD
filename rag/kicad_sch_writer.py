#!/usr/bin/env python3
import uuid
import os

def gen_uuid():
    return str(uuid.uuid4())

def mm(val):
    return f"{val:.2f}"

class KicadSchematic:
    def __init__(self, title="Generated Schematic", company="SRM IST"):
        self.title = title
        self.company = company
        self.symbols = []
        self.wires = []
        self.labels = []
        self.power_symbols = []
        self.junctions = []
        self.lib_symbols = {}
        self.no_connects = []

    def add_wire(self, x1, y1, x2, y2):
        self.wires.append({"x1":x1,"y1":y1,"x2":x2,"y2":y2,"uuid":gen_uuid()})

    def add_net_label(self, name, x, y, angle=0):
        self.labels.append({"name":name,"x":x,"y":y,"angle":angle,"uuid":gen_uuid()})

    def add_power_symbol(self, name, x, y, rotation=0):
        self.power_symbols.append({"name":name,"x":x,"y":y,"rotation":rotation,"uuid":gen_uuid()})

    def add_junction(self, x, y):
        self.junctions.append({"x":x,"y":y,"uuid":gen_uuid()})

    def add_no_connect(self, x, y):
        self.no_connects.append({"x":x,"y":y,"uuid":gen_uuid()})

    def add_symbol_instance(self, lib_id, ref, value, x, y, rotation=0,
                            footprint="", datasheet="", fields=None):
        self.symbols.append({
            "lib_id":lib_id,"ref":ref,"value":value,
            "x":x,"y":y,"rotation":rotation,
            "footprint":footprint,"datasheet":datasheet,
            "fields":fields or {},"uuid":gen_uuid()
        })

    def _resistor_lib(self):
        return '''    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.032) (end 1.016 2.032) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.778) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.778) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

    def _capacitor_lib(self):
        return '''    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 1.651 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "C" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0.9652 -2.5908 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 3.048) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 3.048) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

    def _vdd_lib(self):
        return '''    (symbol "power:VDD_3V3" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -1.27 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "VDD_3V3" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "VDD_3V3_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "VDD_3V3_1_1"
        (pin power_in line (at 0 0 270) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

    def _gnd_lib(self):
        return '''    (symbol "power:GND" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -1.27 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
          (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

    def serialize(self):
        sch_uuid = gen_uuid()
        out = []
        out.append(f'(kicad_sch (version 20230121) (generator skidl_exporter)')
        out.append(f'  (uuid {sch_uuid})')
        out.append(f'  (paper "A4")')
        out.append(f'  (title_block (title "{self.title}") (company "{self.company}"))')
        out.append(f'  (lib_symbols')
        out.append(self._vdd_lib())
        out.append(self._gnd_lib())
        out.append(self._resistor_lib())
        out.append(self._capacitor_lib())
        for sym_def in self.lib_symbols.values():
            out.append(sym_def)
        out.append(f'  )')

        for w in self.wires:
            out.append(f'  (wire (pts (xy {mm(w["x1"])} {mm(w["y1"])}) (xy {mm(w["x2"])} {mm(w["y2"])})) (stroke (width 0) (type solid)) (uuid {w["uuid"]}))')

        for j in self.junctions:
            out.append(f'  (junction (at {mm(j["x"])} {mm(j["y"])}) (diameter 0) (color 0 0 0 0) (uuid {j["uuid"]}))')

        for nc in self.no_connects:
            out.append(f'  (no_connect (at {mm(nc["x"])} {mm(nc["y"])}) (uuid {nc["uuid"]}))')

        for lbl in self.labels:
            out.append(f'  (label "{lbl["name"]}" (at {mm(lbl["x"])} {mm(lbl["y"])} {lbl["angle"]}) (fields_autoplaced) (effects (font (size 1.524 1.524)) (justify left bottom)) (uuid {lbl["uuid"]}))')

        for p in self.power_symbols:
            pwr_uuid = gen_uuid()
            name = p["name"]
            x,y,rot = p["x"],p["y"],p["rotation"]
            val_y = y - 2.54 if rot == 0 else y + 2.54
            out.append(f'''  (symbol (lib_id "power:{name}") (at {mm(x)} {mm(y)} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {p["uuid"]})
    (property "Reference" "#PWR" (at {mm(x)} {mm(y+1.27)} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{name}" (at {mm(x)} {mm(val_y)} 0) (effects (font (size 1.27 1.27))))
    (pin "1" (uuid {gen_uuid()}))
    (instances (project "schematic" (path "/{pwr_uuid}" (reference "#PWR") (unit 1))))
  )''')

        for s in self.symbols:
            inst_uuid = gen_uuid()
            x,y = s["x"],s["y"]
            out.append(f'''  (symbol (lib_id "{s["lib_id"]}") (at {mm(x)} {mm(y)} {s["rotation"]}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {s["uuid"]})
    (property "Reference" "{s["ref"]}" (at {mm(x+2)} {mm(y-2)} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{s["value"]}" (at {mm(x+2)} {mm(y)} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{s["footprint"]}" (at {mm(x)} {mm(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "{s["datasheet"]}" (at {mm(x)} {mm(y)} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {gen_uuid()}))
    (instances (project "schematic" (path "/{inst_uuid}" (reference "{s["ref"]}") (unit 1))))
  )''')

        out.append(')')
        return '\n'.join(out)

    def save(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.serialize())
        print(f"Saved: {filepath}")
