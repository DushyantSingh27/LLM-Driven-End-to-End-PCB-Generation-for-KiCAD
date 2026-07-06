"""
kicad_sch_builder.py
A reusable, tested builder for generating native KiCad 9 .kicad_sch files.
Uses kicad_symbol_parser for exact pin positions, handles:
- Unique reference counting (no duplicate C1, R1 etc)
- Automatic PWR_FLAG placement per unique power net
- Automatic no-connect markers on all unused pins
- Correct Y-axis inversion for screen coordinates
"""
import uuid
from kicad_symbol_parser import load_symbol


def gu():
    return str(uuid.uuid4())


R_SYM = '''(symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
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

C_SYM = '''(symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
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

VDD_SYM = '''(symbol "power:VDD_3V3" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
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

GND_SYM = '''(symbol "power:GND" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -1.27 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

PWRFLAG_SYM = '''(symbol "power:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#FLG" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "PWR_FLAG_0_1"
        (pin power_out line (at 0 0 270) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''


class SchematicBuilder:
    """
    Builds a complete, valid .kicad_sch file with automatic:
    - unique reference numbering
    - PWR_FLAG per unique power net
    - no-connect markers on every unused IC pin
    """

    def __init__(self, title, company, project_name="generated"):
        self.title = title
        self.company = company
        self.project_name = project_name
        self.root_uuid = gu()

        self.lib_symbols = {}
        self.ics = {}
        self.parts = []
        self.wires = []
        self.labels = []
        self.no_connects = []
        self.power_syms = []
        self.power_nets_used = set()

        self._ref_counters = {}
        self._pwr_counter = 0

        from symbol_resolver import resolve_kicad_symbol_dir
        import os as _os
        _symdir = resolve_kicad_symbol_dir()
        _dev = _os.path.join(_symdir, "Device.kicad_sym")
        _pwr = _os.path.join(_symdir, "power.kicad_sym")
        # Authoritative sliced text so embedded copies byte-match KiCad's
        # library (eliminates lib_symbol_mismatch). VDD_3V3 stays on VDD_SYM
        # for now: KiCad's power lib has no "VDD_3V3" symbol (handled separately).
        self.lib_symbols["Device:R"] = self._embed_from_library("Device:R", _dev, "R")
        self.lib_symbols["Device:C"] = self._embed_from_library("Device:C", _dev, "C")
        self.lib_symbols["power:VDD_3V3"] = VDD_SYM
        self.lib_symbols["power:GND"] = self._embed_from_library("power:GND", _pwr, "GND")
        self.lib_symbols["power:PWR_FLAG"] = self._embed_from_library("power:PWR_FLAG", _pwr, "PWR_FLAG")

    def next_ref(self, prefix):
        self._ref_counters[prefix] = self._ref_counters.get(prefix, 0) + 1
        return f"{prefix}{self._ref_counters[prefix]}"

    def next_pwr_ref(self):
        self._pwr_counter += 1
        return f"#PWR{self._pwr_counter:03d}"

    def add_ic(self, ref, symbol_filepath, lib_name, lib_id, x, y,
               footprint="", datasheet="", value=None):
        sym = load_symbol(symbol_filepath, lib_name)
        original_name = sym.symbol_name
        value = value or original_name

        raw = sym.raw_text
        # Top-level symbol definition uses the full lib_id (Library:Component)
        raw = raw.replace(f'(symbol "{original_name}"', f'(symbol "{lib_id}"')
        # Sub-symbols (_0_1, _1_1) must use ONLY the component name, no library prefix
        component_only = lib_id.split(":")[-1]
        raw = raw.replace(f'"{original_name}_0_1"', f'"{component_only}_0_1"')
        raw = raw.replace(f'"{original_name}_1_1"', f'"{component_only}_1_1"')
        self.lib_symbols[lib_id] = raw

        u = gu(); pu = gu()
        self.parts.append(f'''  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {u})
    (property "Reference" "{ref}" (at {x+2:.2f} {y-2:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{value}" (at {x+2:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "{datasheet}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (instances (project "{self.project_name}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))
  )''')

        self.ics[ref] = {
            "symbol": sym,
            "x": x, "y": y,
            "lib_id": lib_id,
            "used_pins": set()
        }
        return ref

    def pin_endpoint(self, ref, pin_number, extra_length=0):
        ic = self.ics[ref]
        pin = ic["symbol"].get_pin(number=pin_number)
        if pin is None:
            raise ValueError(f"Pin {pin_number} not found on {ref}")
        ic["used_pins"].add(str(pin_number))
        return ic["symbol"].endpoint(pin, ic["x"], ic["y"], extra_length)

    def add_resistor(self, value, x, y, rot=0, footprint="Resistor_SMD:R_0805_2012Metric"):
        # R pin length 1.778, pins at +/-3.81 from center along the axis.
        # KiCad R pin endpoints (connection nodes) are at +/- 3.81 (length+gap) from center.
        ref = self.next_ref("R")
        u = gu(); pu = gu()
        self.parts.append(f'''  (symbol (lib_id "Device:R") (at {x:.2f} {y:.2f} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {u})
    (property "Reference" "{ref}" (at {x+2:.2f} {y-2:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{value}" (at {x+2:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (instances (project "{self.project_name}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))
  )''')
        # Pin connection nodes are 3.81mm from center (pin tip in symbol space)
        if rot == 90:
            # horizontal: pin1 left, pin2 right
            pin1 = (x - 3.81, y)
            pin2 = (x + 3.81, y)
        elif rot == 270:
            pin1 = (x + 3.81, y)
            pin2 = (x - 3.81, y)
        elif rot == 180:
            pin1 = (x, y + 3.81)
            pin2 = (x, y - 3.81)
        else:  # rot == 0, vertical
            pin1 = (x, y - 3.81)
            pin2 = (x, y + 3.81)
        return ref, pin1, pin2

    def add_capacitor(self, value, x, y, rot=0, footprint="Capacitor_SMD:C_0805_2012Metric"):
        ref = self.next_ref("C")
        u = gu(); pu = gu()
        self.parts.append(f'''  (symbol (lib_id "Device:C") (at {x:.2f} {y:.2f} {rot}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {u})
    (property "Reference" "{ref}" (at {x+2:.2f} {y-2:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{value}" (at {x+2:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (instances (project "{self.project_name}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))
  )''')
        # C pin connection nodes at +/- 3.81 from center
        if rot == 90:
            pin1 = (x - 3.81, y)
            pin2 = (x + 3.81, y)
        elif rot == 270:
            pin1 = (x + 3.81, y)
            pin2 = (x - 3.81, y)
        elif rot == 180:
            pin1 = (x, y + 3.81)
            pin2 = (x, y - 3.81)
        else:  # rot == 0, vertical
            pin1 = (x, y - 3.81)
            pin2 = (x, y + 3.81)
        return ref, pin1, pin2

    def add_power(self, net_name, x, y):
        ref = self.next_pwr_ref()
        u = gu(); pu = gu()
        vy = y - 3.81 if net_name == "VDD_3V3" else y + 3.81
        self.power_syms.append(f'''  (symbol (lib_id "power:{net_name}") (at {x:.2f} {y:.2f} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {u})
    (property "Reference" "{ref}" (at {x:.2f} {y+1.27:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{net_name}" (at {x:.2f} {vy:.2f} 0) (effects (font (size 1.27 1.27))))
    (instances (project "{self.project_name}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))
  )''')

        if net_name not in self.power_nets_used:
            self.power_nets_used.add(net_name)
            flag_ref = self.next_pwr_ref()
            fu = gu(); fpu = gu()
            flag_x, flag_y = x - 6, y
            self.power_syms.append(f'''  (symbol (lib_id "power:PWR_FLAG") (at {flag_x:.2f} {flag_y:.2f} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {fu})
    (property "Reference" "{flag_ref}" (at {flag_x:.2f} {flag_y+2:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "PWR_FLAG" (at {flag_x:.2f} {flag_y-2:.2f} 0) (effects (font (size 1.27 1.27))))
    (instances (project "{self.project_name}" (path "/{self.root_uuid}" (reference "{flag_ref}") (unit 1))))
  )''')
            self.wires.append(self._wire(flag_x, flag_y, x, y))

        return ref

    def _wire(self, x1, y1, x2, y2):
        return f'  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type solid)) (uuid {gu()}))'

    def add_wire(self, x1, y1, x2, y2):
        self.wires.append(self._wire(x1, y1, x2, y2))

    def add_label(self, name, x, y, angle=0):
        self.labels.append(
            f'  (label "{name}" (at {x:.2f} {y:.2f} {angle}) (fields_autoplaced) '
            f'(effects (font (size 1.524 1.524)) (justify left bottom)) (uuid {gu()}))'
        )

    def add_no_connect(self, x, y):
        self.no_connects.append(f'  (no_connect (at {x:.2f} {y:.2f}) (uuid {gu()}))')

    def auto_no_connect_unused_pins(self):
        for ref, ic in self.ics.items():
            sym = ic["symbol"]
            for pin in sym.pins:
                if pin["hidden"]:
                    continue
                if pin["number"] in ic["used_pins"]:
                    continue
                ex, ey = sym.endpoint(pin, ic["x"], ic["y"])
                self.add_no_connect(ex, ey)
                ic["used_pins"].add(pin["number"])

    def build(self):
        out = []
        out.append(f'(kicad_sch (version 20230121) (generator skidl_exporter)')
        out.append(f'  (uuid {self.root_uuid})')
        out.append('  (paper "A4")')
        out.append(f'  (title_block (title "{self.title}") (company "{self.company}"))')
        out.append('  (lib_symbols')
        for sym_text in self.lib_symbols.values():
            out.append(f'    {sym_text}')
        out.append('  )')
        out.extend(self.wires)
        out.extend(self.no_connects)
        out.extend(self.labels)
        out.extend(self.power_syms)
        out.extend(self.parts)
        out.append(')')
        return '\n'.join(out)

    def save(self, filepath):
        content = self.build()
        with open(filepath, 'w') as f:
            f.write(content)
        return content


    def add_ic_by_name(self, ref, component_name, x, y,
                       footprint="", datasheet="", value=None, lib_id=None):
        """Resolver-backed IC placement. Takes a component NAME; the resolver
        finds it in KiCad's official libraries, extracts via kiutils (geometry)
        + raw-file (hidden flags), and embeds/places identically to add_ic.
        No .txt files, no hand-maintained library."""
        from symbol_resolver import resolve
        from kicad_symbol_parser import KicadSymbol

        resolved = resolve(component_name)
        # Resolver's footprint is authoritative (from KiCad symbol); it wins
        # over any caller/netlist value, which is hallucination-prone.
        if getattr(resolved, "footprint", None):
            footprint = resolved.footprint
        sym = KicadSymbol.from_kiutils(
            resolved._symbol_obj, resolved.library_nickname,
            lib_path=resolved.library_path
        )

        original_name = sym.symbol_name
        if lib_id is None:
            lib_id = f"{resolved.library_nickname}:{original_name}"
        value = value or original_name

        # Embed authoritative sliced text (byte-matches KiCad library ->
        # no lib_symbol_mismatch), via the shared general-rename helper.
        raw = self._embed_from_library(lib_id, resolved.library_path, original_name)
        self.lib_symbols[lib_id] = raw

        u = gu(); pu = gu()
        self.parts.append(f'''  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid {u})
    (property "Reference" "{ref}" (at {x+2:.2f} {y-2:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{value}" (at {x+2:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "{datasheet}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (instances (project "{self.project_name}" (path "/{self.root_uuid}" (reference "{ref}") (unit 1))))
  )''')

        self.ics[ref] = {
            "symbol": sym,
            "x": x, "y": y,
            "lib_id": lib_id,
            "used_pins": set()
        }
        return ref


    def save_to_folder(self, circuit_name, output_root):
        """Write the schematic into a dedicated per-generation folder.

        Creates output_root/circuit_name/ and writes circuit_name.kicad_sch
        there. Returns the full path. The KiCad PROJECT file (.kicad_pro) is
        deliberately NOT emitted here -- it is KiCad-owned; the user runs
        File > New Project in this folder and KiCad generates it correctly.
        """
        import os
        folder = os.path.join(output_root, circuit_name)
        os.makedirs(folder, exist_ok=True)
        sch_path = os.path.join(folder, f"{circuit_name}.kicad_sch")
        self.save(sch_path)
        return sch_path


    def _embed_from_library(self, lib_id, library_file, symbol_name):
        """Return authoritative KiCad symbol text renamed to lib_id.
        Slices the raw block from KiCad's library so the embedded copy
        byte-matches the library (no lib_symbol_mismatch). Renames the
        top-level symbol to lib_id and ALL sub-symbols (_N_M) generally."""
        import re
        from kicad_symbol_parser import _slice_symbol_block
        raw = _slice_symbol_block(library_file, symbol_name)
        if not raw:
            raise KeyError(f"{symbol_name} not found in {library_file}")
        component_only = lib_id.split(":")[-1]
        raw = raw.replace(f'(symbol "{symbol_name}"', f'(symbol "{lib_id}"', 1)
        raw = re.sub(
            r'"' + re.escape(symbol_name) + r'(_\d+_\d+)"',
            lambda m: f'"{component_only}{m.group(1)}"',
            raw,
        )
        return raw
