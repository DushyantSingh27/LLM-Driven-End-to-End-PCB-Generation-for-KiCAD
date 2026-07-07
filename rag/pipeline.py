#!/usr/bin/env python3
"""
pipeline.py -- single-command orchestrator for the full generation flow.
    python pipeline.py                 # run with the built-in SPI benchmark task
    python pipeline.py --skip-generate # reuse existing netlist .py (no LLM call)
    python pipeline.py --name my_board # output folder name
Wires the validated stages into ONE command. Stages are unmodified black boxes.
"""
import os
import sys
import argparse
import builtins

RAG_DIR = os.path.expanduser("~/LLM_Driven_Schematic_Gen/rag")
DEFAULT_OUTPUT_ROOT = "/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs"


def _load_circuit_from_netlist(netlist_path):
    from skidl import lib_search_paths, KICAD  # noqa: F401
    symdir = os.environ.get(
        "KICAD_SYMBOL_DIR",
        "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols")
    if symdir not in lib_search_paths[KICAD]:
        lib_search_paths[KICAD].append(symdir)

    src = open(netlist_path).read()
    cleaned = []
    for line in src.split("\n"):
        st = line.strip()
        if st == "from skidl import *":
            continue
        if st.startswith("lib_search_paths"):
            continue
        if st == "ERC()":
            continue
        cleaned.append(line)
    code = "\n".join(cleaned)

    ns = {}
    exec("from skidl import *", ns)
    exec(code, ns)
    return builtins.default_circuit


def run(circuit_name="generated", output_root=DEFAULT_OUTPUT_ROOT,
        skip_generate=False, title="SPI Auto Schematic",
        company="SRM Chip Design Club"):
    os.chdir(RAG_DIR)
    sys.path.insert(0, RAG_DIR)

    import generate_spi_v2
    netlist_path = generate_spi_v2.OUTPUT_PY

    if not skip_generate:
        print(">>> [1/6] Generating netlist (LLM -> SKiDL)...")
        generate_spi_v2.generate()
    else:
        print(">>> [1/6] Skipping generation, reusing existing netlist:",
              netlist_path)
    if not os.path.isfile(netlist_path):
        raise FileNotFoundError(f"netlist not found: {netlist_path}")

    print(">>> [2/6] Loading circuit from netlist...")
    circuit = _load_circuit_from_netlist(netlist_path)

    import netlist_parser, component_model, placement, schematic_emitter
    from kicad_sch_builder import SchematicBuilder

    print(">>> [3/6] Parsing netlist -> nets/pins model...")
    model = netlist_parser.parse_circuit(circuit)
    print(">>> [4/6] Building component model...")
    comps = component_model.build_components(model)
    print(">>> [5/6] Placing components...")
    pl = placement.place_components(comps)
    print(">>> [6/6] Emitting schematic + saving to folder...")
    builder = SchematicBuilder(title, company, project_name=circuit_name)
    result = schematic_emitter.emit_schematic(comps, pl, model, builder)
    builder.build()
    sch_path = builder.save_to_folder(circuit_name, output_root)

    print("\n=== DONE ===")
    print(f"components: {len(comps)}  labels: {result['labels_placed']}  "
          f"NCs: {result['nc_placed']}  power nets: {len(result['power_nets'])}")
    print(f"schematic:  {sch_path}")
    return sch_path


def main():
    ap = argparse.ArgumentParser(description="One-command PCBSchemaGen pipeline")
    ap.add_argument("--name", default="spi_auto")
    ap.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    ap.add_argument("--skip-generate", action="store_true")
    args = ap.parse_args()
    run(circuit_name=args.name, output_root=args.output_root,
        skip_generate=args.skip_generate)


if __name__ == "__main__":
    main()
