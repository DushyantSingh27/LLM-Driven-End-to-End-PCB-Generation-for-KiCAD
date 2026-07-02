"""
kicad_symbol_parser.py
Parses raw KiCad 9 symbol definitions into structured pin data.
"""
import re

class KicadSymbol:
    def __init__(self, raw_text, lib_name, symbol_name):
        self.raw_text = raw_text
        self.lib_name = lib_name
        self.symbol_name = symbol_name
        self.pins = []
        self._parse()

    def _parse(self):
        pin_pattern = re.compile(
            r'\(pin\s+(\S+)\s+\S+\s*'
            r'\(at\s+([\d\.\-]+)\s+([\d\.\-]+)\s+(\d+)\)\s*'
            r'\(length\s+([\d\.]+)\)\s*'
            r'(?:\(hide\s+yes\)\s*)?'
            r'\(name\s+"([^"]+)"',
            re.MULTILINE
        )
        number_pattern = re.compile(r'\(number\s+"([^"]+)"')

        idx = 0
        while True:
            pin_start = self.raw_text.find("(pin ", idx)
            if pin_start == -1:
                break
            depth = 0
            i = pin_start
            while i < len(self.raw_text):
                if self.raw_text[i] == "(":
                    depth += 1
                elif self.raw_text[i] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            pin_block = self.raw_text[pin_start:i+1]
            idx = i + 1

            m = pin_pattern.search(pin_block)
            if not m:
                continue
            ptype, x, y, angle, length, name = m.groups()
            num_m = number_pattern.search(pin_block)
            number = num_m.group(1) if num_m else "?"
            hidden = "(hide yes)" in pin_block

            self.pins.append({
                "type": ptype,
                "x": float(x),
                "y": float(y),
                "angle": int(angle),
                "length": float(length),
                "name": name,
                "number": number,
                "hidden": hidden
            })

    def get_pin(self, number=None, name=None):
        for p in self.pins:
            if number is not None and p["number"] == str(number):
                return p
            if name is not None and p["name"] == name:
                return p
        return None

    def get_pins_by_name_contains(self, substr):
        return [p for p in self.pins if substr in p["name"]]

    def endpoint(self, pin, ic_x, ic_y, extra_length=0):
        """Calculate the screen-space CONNECTION POINT for a pin.

        In KiCad, a pin's (at x y angle) IS the connection node where wires
        attach. The pin 'length' only describes how far the pin line is drawn
        toward the symbol body and must NOT be added to the connection point.

        Uses Y-axis inversion: screen_y = ic_y - sym_y
        extra_length, if given, extends the wire stub OUTWARD from the pin
        (away from the body) for routing convenience.
        """
        screen_x = ic_x + pin["x"]
        screen_y = ic_y - pin["y"]
        if extra_length == 0:
            return screen_x, screen_y
        # Optional outward extension in the pin's pointing direction
        angle = pin["angle"]
        if angle == 0:
            return screen_x - extra_length, screen_y
        elif angle == 180:
            return screen_x + extra_length, screen_y
        elif angle == 270:
            return screen_x, screen_y - extra_length
        elif angle == 90:
            return screen_x, screen_y + extra_length
        else:
            raise ValueError(f"Unsupported pin angle: {angle}")

    def all_pin_numbers(self):
        return set(p["number"] for p in self.pins)


def load_symbol(filepath, lib_name, expected_symbol_name=None):
    """Load and parse a KiCad symbol file."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read().replace("\r\n", "\n").replace("\r", "\n").strip()

    first_line_match = re.match(r'\(symbol\s+"([^"]+)"', content)
    symbol_name = first_line_match.group(1) if first_line_match else expected_symbol_name

    return KicadSymbol(content, lib_name, symbol_name)




# ============================================================
# kiutils integration (appended - does not modify anything above)
# Geometry/name/number/type/length from kiutils (verified identical to regex
# parser on 14- and 72-pin parts). Hidden flag from the ORIGINAL library file
# sliced to the symbol, because kiutils drops (hide yes) entirely on parse and
# re-serialization - verified against ground truth (B1,J2,J9).
# ============================================================

def _slice_symbol_block(lib_path, symbol_name):
    """Slice the (symbol "NAME" ...) block from a full .kicad_sym by paren-match."""
    with open(lib_path, encoding="utf-8") as fh:
        raw = fh.read()
    marker = f'(symbol "{symbol_name}"'
    start = raw.find(marker)
    if start == -1:
        return ""
    depth = 0
    i = start
    while i < len(raw):
        if raw[i] == '(':
            depth += 1
        elif raw[i] == ')':
            depth -= 1
            if depth == 0:
                break
        i += 1
    return raw[start:i+1]


def _hidden_map_from_sexpr(raw_text):
    """Per-pin hidden flags from raw symbol S-expr text (authoritative)."""
    result = {}
    idx = 0
    while True:
        i = raw_text.find('(pin ', idx)
        if i == -1:
            break
        depth = 0
        j = i
        while j < len(raw_text):
            if raw_text[j] == '(':
                depth += 1
            elif raw_text[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = raw_text[i:j+1]
        idx = j + 1
        num_m = re.search(r'\(number\s+"([^"]+)"', block)
        if num_m:
            result[num_m.group(1)] = '(hide yes)' in block
    return result


def _kicad_symbol_from_kiutils(cls, kiutils_symbol, lib_name, lib_path=None):
    """Build a KicadSymbol from a kiutils Symbol object (same .pins shape)."""
    obj = cls.__new__(cls)
    obj.lib_name = lib_name
    obj.symbol_name = kiutils_symbol.entryName or (
        kiutils_symbol.libId.split(":")[-1] if kiutils_symbol.libId else None
    )
    obj.raw_text = kiutils_symbol.to_sexpr()
    obj.pins = []
    hidden_map = {}
    if lib_path:
        block = _slice_symbol_block(lib_path, obj.symbol_name)
        hidden_map = _hidden_map_from_sexpr(block)
    for unit in kiutils_symbol.units:
        for p in unit.pins:
            num = str(p.number)
            obj.pins.append({
                "type": p.electricalType,
                "x": float(p.position.X),
                "y": float(p.position.Y),
                "angle": int(p.position.angle),
                "length": float(p.length),
                "name": p.name,
                "number": num,
                "hidden": hidden_map.get(num, False),
            })
    return obj

KicadSymbol.from_kiutils = classmethod(_kicad_symbol_from_kiutils)
