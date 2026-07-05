
import sys
import os
import logging
kicad_sym_dir = "/usr/share/kicad/symbols"
if os.path.exists(kicad_sym_dir):
    os.environ["KICAD_SYMBOL_DIR"] = kicad_sym_dir
    os.environ["KICAD9_SYMBOL_DIR"] = kicad_sym_dir
    os.environ["KICAD8_SYMBOL_DIR"] = kicad_sym_dir
    os.environ["KICAD7_SYMBOL_DIR"] = kicad_sym_dir
    os.environ["KICAD6_SYMBOL_DIR"] = kicad_sym_dir

kicad_fp_dir = "/usr/share/kicad/footprints"
if os.path.exists(kicad_fp_dir):
    os.environ["KICAD_FOOTPRINT_DIR"] = kicad_fp_dir
    os.environ["KICAD9_FOOTPRINT_DIR"] = kicad_fp_dir
    os.environ["KICAD8_FOOTPRINT_DIR"] = kicad_fp_dir
    os.environ["KICAD7_FOOTPRINT_DIR"] = kicad_fp_dir
    os.environ["KICAD6_FOOTPRINT_DIR"] = kicad_fp_dir

from skidl import *
from skidl import lib_search_paths, footprint_search_paths, KICAD

TASK_ID = 2
lib_path = r"/teamspace/studios/this_studio/PCBSchemaGen/library"
if os.path.exists(lib_path):
    if KICAD in lib_search_paths:
        if lib_path not in lib_search_paths[KICAD]:
            lib_search_paths[KICAD].append(lib_path)
    else:
         lib_search_paths[KICAD] = [lib_path]
    fp_paths = footprint_search_paths.get(KICAD, [])
    if isinstance(fp_paths, list):
        if lib_path not in fp_paths:
            fp_paths.append(lib_path)
            footprint_search_paths[KICAD] = fp_paths
    else:
        if fp_paths:
            if lib_path != fp_paths:
                footprint_search_paths[KICAD] = [fp_paths, lib_path]
        else:
            footprint_search_paths[KICAD] = [lib_path]

from skidl import *
vin = Net("VIN")
gnd = Net("GND")
vout = Net("VOUT")
r1 = Part("test", "R", value="10k", footprint="test:R_0805")
r2 = Part("test", "R", value="10k", footprint="test:R_0805")
vin += r1[1]
r1[2] += r2[1]
r2[2] += gnd
vout += r1[2]
ERC()


# Artifact Generation
import os
errors = []

try:
    ERC()
except Exception:
    pass # Already checked

try:
    generate_netlist(tool=KICAD9)
except Exception as e:
    errors.append(f"NETLIST: {e}")

try:
    generate_svg()
except Exception as e:
    errors.append(f"SVG: {e}")

try:
    fp_libs = []
    test_pretty = os.path.join(lib_path, "test.pretty")
    if os.path.isdir(test_pretty):
        fp_libs.append(test_pretty)
    if os.path.isdir(lib_path):
        fp_libs.append(lib_path)
    pcb_file = f"extracted_task_{TASK_ID}.kicad_pcb"
    generate_pcb(pcb_file=pcb_file, fp_libs=fp_libs or None)
except Exception as e:
    errors.append(f"PCB: {e}")

if errors:
    print("ARTIFACT_ERROR_START")
    for msg in errors:
        print(msg)
    print("ARTIFACT_ERROR_END")
    raise SystemExit(1)
