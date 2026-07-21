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
    # Decoupling caps belong to the POWER WIRING, not the passive grid: each is
    # drawn inside a T-junction beside the pin it serves, or in the supply
    # region for label-connected rails. Exclude them from the grid.
    import power_wiring as pw
    pcaps = placement.power_cap_refs(comps)          # {cap_ref: rail}
    pl = placement.place_components(comps, skip=pcaps.keys())

    # Split each rail's caps: ONE per wired pin goes in that pin's T-junction;
    # every surplus cap (and every cap of a LABELED rail) goes to the supply
    # region, connected by net-label.
    rail_caps = {}
    for cref, rail in pcaps.items():
        rail_caps.setdefault(rail, []).append(
            (cref, comps[cref].get("value") or "100nF"))
    for rail in rail_caps:
        rail_caps[rail].sort()

    wired_pin_count = {}
    for ref, comp in comps.items():
        if comp["kind"] != "ic":
            continue
        rails = pw.supply_rails(comp)
        wired, _labeled = pw.decide(comp, pl[ref], rails)
        for rail, stacks in wired.items():
            wired_pin_count[rail] = wired_pin_count.get(rail, 0) + len(stacks)

    cap_values, region_cap_list = {}, []
    for rail, caps in rail_caps.items():
        n_wired = wired_pin_count.get(rail, 0)
        if n_wired:
            cap_values[rail] = caps[0][1]            # the T-junction cap
        # one cap per wired pin is consumed by the T-junctions; the rest go below
        for _cref, val in caps[n_wired:]:
            region_cap_list.append((rail, val))

    print(">>> [6/6] Emitting schematic + saving to folder...")
    builder = SchematicBuilder(title, company, project_name=circuit_name)
    result = schematic_emitter.emit_schematic(
        comps, pl, model, builder,
        cap_values=cap_values, region_cap_list=region_cap_list)
    builder.build()
    sch_path = builder.save_to_folder(circuit_name, output_root)
    # --- Phase 2: layout (schematic -> netlist -> placed PCB) ---
    pcb_path = None
    try:
        import subprocess
        kcli = "/mnt/c/Program Files/KiCad/9.0/bin/kicad-cli.exe"
        kpy = "/mnt/c/Program Files/KiCad/9.0/bin/python.exe"
        def w(p):
            return subprocess.run(["wslpath", "-w", p], capture_output=True,
                                  text=True, check=True).stdout.strip()
        net_path = sch_path.rsplit(".", 1)[0] + ".net"
        pcb_path = sch_path.rsplit(".", 1)[0] + ".kicad_pcb"
        print(">>> [7/8] Exporting netlist from verified schematic...")
        subprocess.run([kcli, "sch", "export", "netlist",
                        "--output", w(net_path), w(sch_path)], check=True)
        print(">>> [8/8] Layout: place + legalize -> .kicad_pcb ...")
        subprocess.run([kpy, w(os.path.join(RAG_DIR, "layout_pipeline.py")),
                        w(net_path), w(pcb_path)], check=True)
    except Exception as e:
        print("!!! LAYOUT FAILED (schematic still delivered):", repr(e))
        pcb_path = None

    print("\n=== DONE ===")
    print(f"components: {len(comps)}  labels: {result['labels_placed']}  "
          f"NCs: {result['nc_placed']}  power nets: {len(result['power_nets'])}")
    print(f"power wiring: {result['wired_pins']} pins wired/labeled, "
          f"labeled rails: {result['labeled_rails']}, "
          f"region caps: {len(region_cap_list)}")
    print(f"schematic:  {sch_path}")
    if pcb_path:
        print(f"pcb:        {pcb_path}")
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
