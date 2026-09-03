# LLM-Driven End-to-End PCB Generation for KiCad

Turn a natural-language circuit description into an **ERC-clean KiCad 9 schematic** and a **DRC-checked, routed PCB** — headless, no GUI step anywhere in the flow.

Design intent is guided by STMicroelectronics hardware design guidelines, with mentorship from ST engineers on layout practice. Manufacturability limits come from a fabricator's DFM specification. KiCad is treated as the single source of truth for every file format, and KiCad's own ERC and DRC verify the output independently of the code that produced it.

![Routed board](docs/images/routed.png)

```
"STM32L476 talking to an LSM6DSM over SPI"
        │
        ├─ RAG (datasheets) + KiCad symbol resolver   →  authoritative pin table
        ├─ LLM                                        →  SKiDL (Python)
        ├─ SKiDL + ERC                                →  verified netlist
        ├─ placement + ST-style power wiring          →  native .kicad_sch
        ├─ footprints, rules, stitching, pours        →  .kicad_pcb
        ├─ Freerouting (DSN → SES)                    →  routed board
        └─ DRC + independent verifier                 →  report.json, exit 0 or 1
```

**Repo:** `https://github.com/DushyantSingh27/LLM-Driven-End-to-End-PCB-Generation-for-KiCAD`

---

## Table of contents

1. [What you get](#1-what-you-get)
2. [Requirements](#2-requirements)
3. [Install](#3-install)
4. [Configure](#4-configure--paths-you-must-change)
5. [Run the benchmark](#5-run-the-benchmark)
6. [Reading the output](#6-reading-the-output)
7. [Generating **your own** circuit](#7-generating-your-own-circuit)
8. [Troubleshooting](#8-troubleshooting)
9. [Known limits](#9-known-limits)
10. [Verified environment](#10-verified-environment)

---

## 1. What you get

![Pipeline](docs/images/pipeline.png)

The architecture rests on one separation, held throughout: **the language model decides what the circuit is; deterministic code decides what the files are.** The LLM never emits a coordinate, a trace width or a clearance. Conversely, no rule engine guesses which pin is a power pin — that comes from the netlist's own pin semantics.

Running the benchmark end-to-end reproduces this, on an STM32L476JGYxP (WLCSP-72) + LSM6DSM (LGA-14) SPI board:

| Result | Value |
|---|---|
| Components / nets / pads | 22 / 68 / 126 |
| ERC errors | **0** |
| Independent verifier | clean |
| Pads bound to nets | 126 / 126 |
| Courtyard violations | 0 |
| Copper clearance violations | **0** |
| Traces / vias after routing | 94 / 44 |
| Unconnected items | 10 *(see [§9](#9-known-limits) — this is a deliberate trade)* |
| Exit code | `1` (`INCOMPLETE`) |

### Phase 1 output — the generated schematic

Native `.kicad_sch`, opened directly in Eeschema. Power rails auto-wired in ST's drawing style: T-junctions where the stacks fit, net labels where the pin column is crowded.

![Generated schematic](docs/images/schematic.png)

### Phase 2 output — placement and routing

Constructive placement from real ball coordinates, then a force-directed legaliser; routed by Freerouting through the DSN/SES bridge.

![Placed board](docs/images/placed.png)

The pipeline **reports failure honestly**. Exit code `0` means DRC-clean; `1` means something is unresolved and the report says exactly what. Do not treat a non-zero exit as "the tool is broken" — read `report.json`.

---

## 2. Requirements

| | |
|---|---|
| **OS** | Windows 10/11 with **WSL2** (Ubuntu 22.04). The split is required — see below. |
| **Python** | 3.10 (in WSL) — *and* KiCad's own bundled `python.exe` (on Windows) |
| **KiCad** | **9.0.8** on the Windows side |
| **Java** | A JRE on the Windows side, for Freerouting |
| **Freerouting** | `freerouting.jar` |
| **API key** | Anthropic, and/or NVIDIA NIM (has a free tier) |
| **Disk** | ~2 GB (Chroma index + sentence-transformers model) |

### Why two operating systems?

`pcbnew` is a SWIG binding into KiCad's C++ core. It **must** run under the same interpreter KiCad ships with. `pip install`-ing it into a Linux venv gives ABI mismatches that fail in confusing ways — segfaults, or worse, silently wrong numbers.

**The rule:**

- Anything that is **pure logic** (SKiDL, RAG, resolver, netlist parsing, schematic emit) → **WSL Python**
- Anything that **touches a board object** (placement, rules, zones, DSN/SES, DRC) → **KiCad's Windows `python.exe`**

Paths cross with `wslpath -w` going out, and `/mnt/c/...` coming back.

---

## 3. Install

### 3.1 WSL and Python

```bash
# From Windows PowerShell (once):
wsl --install -d Ubuntu-22.04
```

```bash
# Then, inside WSL:
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git

cd ~
git clone https://github.com/DushyantSingh27/LLM-Driven-End-to-End-PCB-Generation-for-KiCAD.git LLM_Driven_Schematic_Gen
cd LLM_Driven_Schematic_Gen

python3 -m venv venv
source venv/bin/activate
python -V          # must print Python 3.10.x
```

> **The clone directory name matters.** Several scripts hardcode `~/LLM_Driven_Schematic_Gen`. Clone into exactly that name, or edit the paths in [§4](#4-configure--paths-you-must-change).

### 3.2 Python dependencies

```bash
pip install skidl==2.2.3
pip install anthropic==0.115.1
pip install openai==2.46.0
pip install pymupdf4llm==1.28.0 pymupdf-layout==1.28.0
pip install chromadb==1.5.9
pip install sentence-transformers==5.6.0
```

> **Do not substitute plain PyMuPDF for `pymupdf4llm`.** Plain extraction turns the STM32 ball-assignment tables into mojibake — which is precisely the data the model most needs. The failure does not appear until three stages later, as an invalid pin name.

### 3.3 KiCad 9

Install **KiCad 9.0.8** from [kicad.org](https://www.kicad.org) (Windows installer). Then verify it from WSL:

```bash
ls "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols/" | head
"/mnt/c/Program Files/KiCad/9.0/bin/python.exe" -c "import pcbnew; print(pcbnew.GetBuildVersion())"
# expect: 9.0.8
```

> ⚠️ **The install path contains a space.** Quote it *everywhere*. Unquoted, it fails silently in about half of all shell contexts.

If your KiCad lives elsewhere, override the symbol directory:

```bash
export KICAD_SYMBOL_DIR="/mnt/c/Path/To/KiCad/9.0/share/kicad/symbols"
```

### 3.4 Freerouting and Java

Install a JRE on the **Windows** side and place the jar somewhere stable, e.g. `C:\tools\freerouting\freerouting.jar`.

```bash
java -version    # confirm the JRE is reachable
```

`rag/routing.py` performs java/jar discovery and drives it headless:

```
java -jar freerouting.jar -de board.dsn -do board.ses
```

> Check which JRE version your Freerouting build requires. Recent releases track new JREs and fail on older ones with an error that does not mention Java.

### 3.5 API keys

```bash
export ANTHROPIC_API_KEY=sk-ant-...      # console.anthropic.com
export NVIDIA_API_KEY=nvapi-...          # build.nvidia.com  (only if PROVIDER="nvidia")
```

Add them to `~/.bashrc` so they survive a new shell.

> **A Claude Pro subscription is not API access.** The API bills separately.

---

## 4. Configure — paths you must change

These are hardcoded. Change them, or match them.

| File | Constant | Default | Action |
|---|---|---|---|
| `rag/pipeline.py` | `DEFAULT_OUTPUT_ROOT` | `/mnt/c/Users/Dushyant/Desktop/pcbgen_outputs` | **Must change** — or always pass `--output-root` |
| `rag/build_rag_v2.py` | `DATASHEET_DIR` | `~/LLM_Driven_Schematic_Gen/datasheets` | OK if you cloned to that name |
| `rag/build_rag_v2.py` | `CHROMA_DIR` | `~/LLM_Driven_Schematic_Gen/rag/chroma_db` | OK if you cloned to that name |
| `rag/build_rag_v2.py` | `COLLECTION` | `st_datasheets_v2` | Leave alone unless you keep multiple corpora |
| `rag/generate_spi_v2.py` | `PROVIDER` | `"anthropic"` | Set to the provider whose key you have |
| `rag/generate_spi_v2.py` | `MODEL` | `claude-sonnet-4-6` | Change to switch Anthropic model |
| `rag/generate_spi_v2.py` | `NVIDIA_MODEL` | `z-ai/glm-5.2` | Used when `PROVIDER` is NVIDIA |
| `rag/generate_spi_v2.py` | `OUTPUT_PY` | `rag/lsm6dsm_stm32l476_spi_v2.py` | Where the generated SKiDL is written |
| *(env)* | `KICAD_SYMBOL_DIR` | KiCad 9 default path | Set only if KiCad is installed elsewhere |

The output root must be a **Windows-visible** path (under `/mnt/c/...`), because Phase 2 runs under Windows Python and has to read what Phase 1 wrote.

---

## 5. Run the benchmark

### Step 1 — Build the RAG index *(once per datasheet set)*

Put component datasheet PDFs in `datasheets/`. The filename becomes the component key:

```
datasheets/STM32L476.pdf   →  component "STM32L476"
datasheets/LSM6DSM.pdf     →  component "LSM6DSM"
```

```bash
source ~/LLM_Driven_Schematic_Gen/venv/bin/activate
cd ~/LLM_Driven_Schematic_Gen/rag
python build_rag_v2.py
```

Extracts with `pymupdf4llm` (layout-aware markdown), splits on `#`/`##`/`###`, chunks at 1200 chars with 120 overlap, embeds, and writes a persistent Chroma collection to `rag/chroma_db`.

### Step 2 — Phase 1: prompt → verified schematic

```bash
python pipeline.py --name spi_auto --output-root /mnt/c/Users/<YOU>/Desktop/pcbgen_outputs
```

One command. It runs generation (LLM → SKiDL → ERC), then the serialiser (netlist → placement → ST-style power wiring → `.kicad_sch`), then verification.

```bash
# Re-run the serialiser on the last generated netlist, without paying for tokens:
python pipeline.py --name spi_auto --skip-generate
```

`--skip-generate` is the flag you will use most. Use it whenever you are debugging the serialiser rather than the model.

### Step 3 — Phase 2: netlist → routed board

Launch this with **KiCad's Windows Python**, not the venv:

```bash
RUN=/mnt/c/Users/<YOU>/Desktop/pcbgen_outputs/spi_auto

"/mnt/c/Program Files/KiCad/9.0/bin/python.exe" \
  "$(wslpath -w ~/LLM_Driven_Schematic_Gen/rag/layout_pipeline.py)" \
  "$(wslpath -w $RUN/spi_auto.net)" \
  "$(wslpath -w $RUN)"

echo "exit code: $?"     # 0 = DRC clean, 1 = incomplete
```

`layout_pipeline.py` takes exactly **two positional arguments**: the netlist path and the output directory. Both must be **Windows-style** paths.

---

## 6. Reading the output

`run_context.py` gives every run its own directory with structural uniqueness:

| Artifact | What it is |
|---|---|
| `board.kicad_pcb` | The board — open it in pcbnew |
| `board.dsn` | What was handed to the router |
| `board.ses` | What the router handed back |
| `drc.rpt` | KiCad's own DRC report |
| `router.log` | Freerouting's output, parsed for the unrouted count |
| `report.json` | **Start here.** Stage-by-stage results, not just a verdict. |

The console log is stage-numbered (`[L1/12] … [L12/12]`) and names anything it could not do rather than dropping it silently — e.g. `UNREACHABLE U1 pad H8 (/VDD_3V3)`.

---

## 7. Generating your own circuit

The benchmark is not special. To generate a different board:

### 7.1 Add the datasheets

```bash
cp MY_MCU.pdf MY_SENSOR.pdf ~/LLM_Driven_Schematic_Gen/datasheets/
cd ~/LLM_Driven_Schematic_Gen/rag
python build_rag_v2.py        # rebuild the index
```

### 7.2 Edit the spec in `rag/generate_spi_v2.py`

Three constants define the circuit:

```python
USER_TASK  = "..."     # the natural-language spec, e.g. "connect X to Y over I2C
                       #  with pull-ups, decouple every supply rail"
COMPONENTS = {...}     # part number → KiCad symbol/library mapping
RAG_QUERIES = [...]    # what to retrieve from the datasheets before prompting
```

`RAG_QUERIES` is the one people under-invest in. The model is only as grounded as what you retrieve. For a new part, query for the **ball/pin assignment table**, the **supply rail list**, and the **decoupling recommendations** at minimum.

There are worked examples in the repo for other topologies: `generate_i2c_circuit.py`, `generate_st_circuit.py`.

### 7.3 Run it

```bash
python pipeline.py --name my_board --output-root /mnt/c/Users/<YOU>/Desktop/pcbgen_outputs
```

then Phase 2 as in [§5 step 3](#step-3--phase-2-netlist--routed-board).

### 7.4 Expect to hit the generalisation gaps

Be aware before you start (details in [§9](#9-known-limits)):

- The placer contains **circuit-specific reference designators**. A different topology can trip them.
- Net names must match the pipeline's **contract** (`GND`, `VDD_3V3`, `VREF_PLUS`, …). A model that emits `VSS` or `VREF+` will break the power-wiring stage.
- Only **single-sided** placement is supported.

---

## 8. Troubleshooting

**`ImportError: No module named pcbnew`**
You ran Phase 2 with the venv Python. Use KiCad's `python.exe`.

**Design rules look wrong / clearance numbers don't match what you set**
KiCad 9 stores netclass **definitions** in the `.kicad_pro` project file, not the `.kicad_pcb`, and `SaveBoard` will not overwrite an existing project file. A stale `.kicad_pro` silently overrides your computed rules and invalidates every measurement taken afterwards. `save_board` clears them — but if you are writing your own stage, delete the project file before saving.

**Python exits with no traceback during the pour stage**
`ZONE_FILLER` hard-crashes at the C++ level on an in-memory board. `BuildConnectivity()` does not help. There is a deliberate **save/reload seam** before pouring; do not remove it.

**Netclasses vanish after a save/reload**
Expected — the definitions live in the project file. This is why DSN clearance inflation is done **in memory** and reverted immediately, rather than via a round-trip.

**A shell command "does nothing"**
You did not quote `"/mnt/c/Program Files/KiCad/9.0/..."`.

**The router succeeds but KiCad's DRC rejects the board**
DSN carries copper-to-copper clearance; it does **not** carry KiCad's hole-to-copper rule. The exported clearance is inflated so one implies the other:

```
c_router = max(c_copper, c_hole + r_hole − r_via) = 0.1250 mm
```

**Invalid pin names in the generated SKiDL**
Your RAG index is probably built from mangled extraction. Confirm `pymupdf4llm` is installed (not plain PyMuPDF) and rebuild.

---

## 9. Known limits

Stated plainly, because a pipeline that oversells itself moves error discovery to the fab.

**10 unconnected items — a measured trade, not a bug.**
All ten are WLCSP-72 inner-ball escape routes. At 0.4 mm ball pitch the keep-out ring leaves no legal channel for a through-via to reach U1's inner balls. The clearance choice was measured, not guessed:

| Router clearance | Unrouted | Hole violations |
|---|---|---|
| 0.09 mm | 6 | **14** |
| **0.1250 mm** | **10** | **0** |

The 0.09 mm board connects four more nets and is **not manufacturable**. The pipeline takes the manufacturable board. Closing the remaining ten is a *stackup* decision — microvias or more layers — not a router tuning problem.

**No intentional trace widths.** `m_TrackMinWidth` is a DRC minimum, not the width the router uses. Netclasses with real per-class widths are not implemented yet, so trace widths are the DSN default.

**Single-sided placement only.** The placer has no concept of a bottom side.

**Circuit-specific hardcodes in placement.** Some reference designators are baked in.

**No generation-contract normalisation.** `VSS`/`GND`, `VDD`/`VDD_3V3`, `VREF+`/`VREF_PLUS`, `100n`/`100nF` are not yet unified.

**Silkscreen placement not implemented.** 10 silkscreen warnings are deferred; they are cosmetic.

**LLM stage is not reproducible on Anthropic.** No seed is exposed. NVIDIA NIM does expose one.

**Freerouting is heuristic.** Runs may route differently; the DRC verdict has been stable in practice.

---

## 10. Verified environment

This exact combination is what the results above were produced on.

| Component | Version |
|---|---|
| KiCad / `pcbnew` | **9.0.8** |
| OS | Ubuntu 22.04 (WSL2) |
| Python | 3.10 |
| `skidl` | 2.2.3 |
| `anthropic` | 0.115.1 |
| `openai` | 2.46.0 |
| `pymupdf` | 1.28.0 |
| `pymupdf-layout` | 1.28.0 |
| `pymupdf4llm` | 1.28.0 |
| `chromadb` | 1.5.9 |
| `sentence-transformers` | 5.6.0 |

**Not yet pinned** — record these yourself, they silently change results:
Freerouting jar version · JRE version · fab DFM spec revision.

`pcbnew` is a binding to a *specific* KiCad build. A minor version bump can change enum names, default clearances, or whether a call exists — and the failure shows up as a wrong **number**, not an exception. Pin it.

---

## Design principle

> **The language model decides what the circuit is. Deterministic code decides what the files are.**

The LLM never emits a coordinate, a trace width or a clearance. No model output reaches a file without passing a machine check, and there are always **two independent judges** — the authoritative tool (ERC, DRC) *and* an independent verifier that reads geometry rather than intent. Neither is trusted alone.

A disappearing ERC error is worse news than a new one: it means two nets silently merged, and the check that would have complained is now satisfied by the short itself.

---

## Acknowledgements

Built by **Dushyant Singh**, mentored by **Saurabh Rawat**, STMicroelectronics.
