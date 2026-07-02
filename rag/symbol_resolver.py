"""
symbol_resolver.py  --  Module 3: the stable symbol-resolution interface.

CONTRACT (never changes):
    resolve(component_name) -> ResolvedSymbol

Everything downstream (SKiDL netlist generation, the .kicad_sch builder)
asks this module for symbols. Nothing hand-edits a library file, ever.
"""

import os
import glob
import subprocess
from dataclasses import dataclass, field
from typing import Optional, List

from kiutils.symbol import SymbolLib


_DEFAULT_KICAD_PATHS = [
    "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols",
    "/usr/share/kicad/symbols",
    "/mnt/c/Program Files/KiCad/10.0/share/kicad/symbols",
]


def _dir_has_symbols(path: str) -> bool:
    return os.path.isdir(path) and bool(glob.glob(os.path.join(path, "*.kicad_sym")))


def resolve_kicad_symbol_dir(explicit: Optional[str] = None) -> str:
    candidates: List[str] = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("KICAD_SYMBOL_DIR")
    if env:
        candidates.append(env)
    candidates.extend(_DEFAULT_KICAD_PATHS)

    for path in candidates:
        if _dir_has_symbols(path):
            return path

    raise FileNotFoundError(
        "No valid KiCad symbol directory found. Checked (in order): "
        + "; ".join(candidates)
        + ". A directory qualifies only if it exists and contains .kicad_sym "
        "files. Set KICAD_SYMBOL_DIR to your KiCad symbols folder, e.g. "
        "'/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols'."
    )


@dataclass
class ResolvedSymbol:
    component_name: str
    library_nickname: str
    library_path: str
    symbol_text: str
    pin_count: int
    extends: Optional[str] = None
    _symbol_obj: object = field(default=None, repr=False)


class SymbolResolver:
    def __init__(self, symbol_dir: Optional[str] = None):
        self.symbol_dir = resolve_kicad_symbol_dir(symbol_dir)
        self._cache = {}

    def _find_library_for(self, component_name: str) -> Optional[str]:
        pattern = f'(symbol "{component_name}"'
        try:
            out = subprocess.run(
                ["grep", "-rlF", pattern, self.symbol_dir],
                capture_output=True, text=True, timeout=60,
            )
            files = [f for f in out.stdout.splitlines() if f.endswith(".kicad_sym")]
            return files[0] if files else None
        except (subprocess.SubprocessError, FileNotFoundError):
            for path in glob.glob(os.path.join(self.symbol_dir, "*.kicad_sym")):
                with open(path, encoding="utf-8") as fh:
                    if pattern in fh.read():
                        return path
            return None

    def resolve(self, component_name: str) -> ResolvedSymbol:
        if component_name in self._cache:
            return self._cache[component_name]

        lib_path = self._find_library_for(component_name)
        if lib_path is None:
            raise KeyError(
                f"Symbol '{component_name}' not found in any .kicad_sym under "
                f"{self.symbol_dir}. (The path is valid and contains libraries, "
                f"so the component name is likely misspelled or in a library "
                f"not present in this KiCad install.)"
            )

        lib = SymbolLib.from_file(lib_path)

        symbol = None
        for sym in lib.symbols:
            name = sym.entryName or (sym.libId.split(":")[-1] if sym.libId else None)
            if name == component_name:
                symbol = sym
                break
        if symbol is None:
            raise KeyError(
                f"'{component_name}' matched file {lib_path} in pre-scan but "
                f"the parser did not find it (name mismatch or nested match)."
            )

        symbol_text = symbol.to_sexpr()
        pin_count = sum(len(unit.pins) for unit in symbol.units)
        lib_nick = os.path.splitext(os.path.basename(lib_path))[0]

        resolved = ResolvedSymbol(
            component_name=component_name,
            library_nickname=lib_nick,
            library_path=lib_path,
            symbol_text=symbol_text,
            pin_count=pin_count,
            extends=symbol.extends,
            _symbol_obj=symbol,
        )
        self._cache[component_name] = resolved
        return resolved


_default_resolver = None

def resolve(component_name: str, symbol_dir: Optional[str] = None) -> ResolvedSymbol:
    global _default_resolver
    if _default_resolver is None or (symbol_dir and _default_resolver.symbol_dir != symbol_dir):
        _default_resolver = SymbolResolver(symbol_dir)
    return _default_resolver.resolve(component_name)


if __name__ == "__main__":
    print(f"Using KiCad symbol dir: {resolve_kicad_symbol_dir()}")
    print()
    for name, expected in [("STM32L476JGYxP", 72), ("LSM6DSM", 14)]:
        try:
            r = resolve(name)
            status = "OK" if r.pin_count == expected else f"CHECK (got {r.pin_count}, expected {expected})"
            print(f"{name}: {r.pin_count} pins from {r.library_nickname} - {status}")
            if r.extends:
                print(f"    (extends: {r.extends})")
        except Exception as e:
            print(f"{name} FAILED: {type(e).__name__}: {e}")
