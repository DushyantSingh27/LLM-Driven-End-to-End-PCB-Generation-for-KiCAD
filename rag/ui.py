#!/usr/bin/env python3
"""
ui.py -- PCBSchemaGen web UI (Streamlit).

    streamlit run ui.py

Minimal, professional one-pager:
  prompt -> Generate -> live "thinking chain" of the 6 pipeline stages
  -> result summary -> copy-ready output folder -> (optional) schematic image.

The pipeline runs as a SUBPROCESS, not in-process: Streamlit keeps the
process alive between clicks, and SKiDL's default_circuit is a process-global
that would accumulate parts across runs. Fresh process per generation avoids
that. Stage progress is parsed live from the ">>> [n/6]" stdout markers.
"""
import os
import re
import subprocess

import streamlit as st

RAG_DIR = os.path.expanduser("~/LLM_Driven_Schematic_Gen/rag")
PYTHON = os.path.expanduser("~/LLM_Driven_Schematic_Gen/venv/bin/python3")
KICAD_CLI = "/mnt/c/Program Files/KiCad/9.0/bin/kicad-cli.exe"

STAGES = [
    "Generating netlist (LLM \u2192 SKiDL)",
    "Loading circuit from netlist",
    "Parsing netlist \u2192 nets/pins model",
    "Resolving symbols & pin geometry",
    "Placing components",
    "Emitting KiCad schematic",
]

st.set_page_config(page_title="PCBSchemaGen", page_icon="\u26a1",
                   layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 780px; }
    h1 { font-weight: 600; letter-spacing: -0.5px; }
    .stage-done { color: #21c354; }
    div[data-testid="stStatusWidget"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("PCBSchemaGen")
st.caption("Natural language \u2192 ERC-validated KiCad schematic \u00b7 "
           "STMicroelectronics parts")

prompt = st.text_area(
    "Circuit description",
    value=("LSM6DSM with STM32L476JGY6 interfaced over SPI. Used Interrupt "
           "pins as well and all the coupling and decoupling capacitors "
           "wherever necessary"),
    height=90,
)

col1, col2 = st.columns([2, 1])
with col1:
    name = st.text_input("Output name", value="spi_auto")
with col2:
    regen = st.toggle("Regenerate netlist (LLM call)", value=False,
                      help="Off: reuse the existing validated netlist. "
                           "On: call the LLM to regenerate it.")

go = st.button("Generate", type="primary", use_container_width=True)


def render_schematic_svg(sch_path):
    """Optional add-on: export schematic to SVG via kicad-cli. Returns the
    SVG path or None on any failure. Never raises."""
    try:
        out_dir = os.path.dirname(sch_path)
        win_sch = subprocess.run(["wslpath", "-w", sch_path],
                                 capture_output=True, text=True,
                                 timeout=10).stdout.strip()
        win_out = subprocess.run(["wslpath", "-w", out_dir],
                                 capture_output=True, text=True,
                                 timeout=10).stdout.strip()
        r = subprocess.run([KICAD_CLI, "sch", "export", "svg",
                            "-o", win_out, win_sch],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return None
        base = os.path.splitext(os.path.basename(sch_path))[0]
        svg = os.path.join(out_dir, base + ".svg")
        return svg if os.path.isfile(svg) else None
    except Exception:
        return None


if go:
    cmd = [PYTHON, os.path.join(RAG_DIR, "pipeline.py"), "--name", name]
    if not regen:
        cmd.append("--skip-generate")

    stage_boxes = [st.empty() for _ in STAGES]
    for i, label in enumerate(STAGES):
        stage_boxes[i].markdown(f"\u25cb {label}")

    log_lines = []
    sch_path = None
    summary = None
    current = -1

    proc = subprocess.Popen(cmd, cwd=RAG_DIR, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        log_lines.append(line.rstrip())
        m = re.search(r">>> \[(\d)/6\]", line)
        if m:
            new = int(m.group(1)) - 1
            if current >= 0:
                stage_boxes[current].markdown(
                    f"<span class='stage-done'>\u2713</span> {STAGES[current]}",
                    unsafe_allow_html=True)
            current = new
            stage_boxes[current].markdown(f"\u25d0 **{STAGES[current]} ...**")
        ms = re.search(r"^schematic:\s+(.*)$", line.strip())
        if ms:
            sch_path = ms.group(1).strip()
        mc = re.search(r"components: (\d+)\s+labels: (\d+)\s+NCs: (\d+)\s+"
                       r"power nets: (\d+)", line)
        if mc:
            summary = mc.groups()
    proc.wait()

    if proc.returncode == 0 and sch_path:
        if current >= 0:
            stage_boxes[current].markdown(
                f"<span class='stage-done'>\u2713</span> {STAGES[current]}",
                unsafe_allow_html=True)
        st.success("Schematic generated \u00b7 ERC-clean pipeline")
        if summary:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Components", summary[0])
            c2.metric("Net labels", summary[1])
            c3.metric("No-connects", summary[2])
            c4.metric("Power nets", summary[3])
        out_folder = os.path.dirname(sch_path)
        try:
            win_folder = subprocess.run(
                ["wslpath", "-w", out_folder], capture_output=True,
                text=True, timeout=10).stdout.strip()
        except Exception:
            win_folder = ""
        st.markdown("**Output folder** (copy \u2192 open in KiCad / Explorer):")
        st.code(win_folder or out_folder, language=None)

        with st.spinner("Rendering schematic preview..."):
            svg = render_schematic_svg(sch_path)
        if svg:
            st.image(svg, use_container_width=True)
        else:
            st.info("Preview render unavailable \u2014 open the .kicad_sch "
                    "in KiCad to view.")
    else:
        if current >= 0:
            stage_boxes[current].markdown(f"\u2717 {STAGES[current]} failed")
        st.error("Pipeline failed \u2014 log below.")

    with st.expander("Pipeline log"):
        st.code("\n".join(log_lines), language=None)
