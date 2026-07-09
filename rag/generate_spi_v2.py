"""
generate_spi_v2.py -- Approach 2 benchmark generation.
Resolver supplies AUTHORITATIVE pins (LLM must pick from inventory - no
hallucination). RAG supplies application knowledge. LLM designs connections.
"""

import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
import anthropic

from kiutils.symbol import SymbolLib
from kicad_symbol_parser import KicadSymbol

CHROMA_DIR = os.path.expanduser("~/LLM_Driven_Schematic_Gen/rag/chroma_db")
MODEL = "claude-sonnet-4-6"
OUTPUT_PY = os.path.expanduser("~/LLM_Driven_Schematic_Gen/rag/lsm6dsm_stm32l476_spi_v2.py")
TOKEN_LOG = os.path.expanduser("~/LLM_Driven_Schematic_Gen/rag/spi_benchmark_tokens.txt")

USER_TASK = (
    "LSM6DSM with STM32L476JGY6 interfaced over SPI. Used Interrupt pins "
    "as well and all the coupling and decoupling capacitors wherever necessary"
)

COMPONENTS = {
    "MCU":    ("MCU_ST_STM32L4", "STM32L476JGYxP", "STM32L476JG"),
    "SENSOR": ("Sensor_Motion",  "LSM6DSM",        "LSM6DSM"),
}

RAG_QUERIES = [
    ("STM32L476JG", "power supply VDD VDDA VDD12 VDDUSB VDDIO2 decoupling scheme"),
    ("STM32L476JG", "SPI1 SPI2 SCK MISO MOSI NSS alternate function"),
    ("STM32L476JG", "NRST BOOT0 reset boot configuration"),
    ("LSM6DSM", "SPI 4-wire mode CS SDX SDO connection"),
    ("LSM6DSM", "INT1 INT2 interrupt pins"),
    ("LSM6DSM", "VDD VDDIO decoupling capacitor application"),
]

KICAD_SYM_DIR = os.environ.get("KICAD_SYMBOL_DIR",
    "/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols")


def load_pins(lib_nick, symbol_name):
    path = os.path.join(KICAD_SYM_DIR, lib_nick + ".kicad_sym")
    lib = SymbolLib.from_file(path)
    ksym = [s for s in lib.symbols if s.entryName == symbol_name][0]
    sym = KicadSymbol.from_kiutils(ksym, lib_nick, lib_path=path)
    return sym.pins


def format_pin_inventory(name, symbol_name, pins):
    lines = [f"### {name} = {symbol_name}  (use ONLY these pin numbers)"]
    for p in sorted(pins, key=lambda x: str(x['number'])):
        lines.append(f"  pin \"{p['number']}\": {p['name']} [{p['type']}]")
    return "\n".join(lines)


def get_rag_context():
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection("st_datasheets_v2", embedding_function=ef)
    out = {"STM32L476JG": [], "LSM6DSM": []}
    for comp, q in RAG_QUERIES:
        res = col.query(query_texts=[q], n_results=2, where={"component": comp})
        for doc in res["documents"][0]:
            if doc not in out[comp]:
                out[comp].append(doc)
    parts = ["=== STM32L476 application notes ==="] + out["STM32L476JG"]
    parts += ["\n=== LSM6DSM application notes ==="] + out["LSM6DSM"]
    return "\n\n".join(parts)


def build_prompt():
    mcu_lib, mcu_name, _ = COMPONENTS["MCU"]
    sen_lib, sen_name, _ = COMPONENTS["SENSOR"]
    mcu_pins = load_pins(mcu_lib, mcu_name)
    sen_pins = load_pins(sen_lib, sen_name)
    inventory = (format_pin_inventory("MCU", mcu_name, mcu_pins) + "\n\n"
                 + format_pin_inventory("SENSOR", sen_name, sen_pins))
    rag = get_rag_context()

    prompt = f"""You are a SKiDL Python code generator for STM32 + MEMS sensor circuits.

AUTHORITATIVE PIN INVENTORY (the REAL pins of each part - use ONLY these exact
pin-number strings; never invent a pin number):

{inventory}

DATASHEET APPLICATION NOTES:
{rag}

TASK:
{USER_TASK}

DESIGN REQUIREMENTS (decide specifics yourself, using ONLY pins above):
- 4-wire SPI between MCU and sensor (SCLK, MOSI, MISO, CS). Choose a real SPI
  peripheral on the MCU; pick its actual ball pins from the inventory (the
  alternate-function names in the notes tell you which balls carry SPI signals).
- Route sensor INT1 and INT2 to suitable MCU GPIO balls from the inventory.
- Configure the LSM6DSM for SPI mode (not I2C).
- Decouple EVERY MCU power rail in the inventory (VDD, VDD12, VDDA, VDDIO2,
  VDDUSB, VBAT, VREF+). This WLCSP72 SMPS variant uses VDD12, NOT VCAP.
  Decouple sensor VDD and VDDIO.
- Handle NRST and BOOT0 correctly.
- Choose standard passive values.

STRICT SKiDL RULES:
- Start EXACTLY with these two lines:
    from skidl import *
    lib_search_paths[KICAD].append("/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols")
- Use Part("MCU_ST_STM32L4", "STM32L476JGYxP") for the MCU.
- Use Part("Sensor_Motion", "LSM6DSM") for the sensor.
- Use Part("Device", "R", value="<val>") for resistors.
- Use Part("Device", "C", value="<val>") for capacitors.
- Nets: Net("NAME"); connections: net += part["PINNUMBER"]
- CRITICAL: index pins by their exact ball-designator STRING from the inventory,
  e.g. mcu["H5"], mcu["A9"], imu["1"], imu["12"]. NEVER use an integer index
  like mcu[20] and NEVER index by pin NAME like mcu["PA5"] (name indexing is
  ambiguous and matches the wrong pin). Ball-designator strings ONLY.
- Unused pins: part["PINNUMBER"] += NC
- End with: ERC()
- Output ONLY Python code, no markdown, no explanation.
"""
    return prompt


def generate():
    prompt = build_prompt()
    print(f"Model: {MODEL}")
    print(f"Prompt length: {len(prompt)} chars")
    print("Generating (Approach 2: authoritative pins + RAG)...\n")

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=("You are a SKiDL Python code generator. Output ONLY valid Python. "
                "Start with 'from skidl import *' and end with 'ERC()'. Use ONLY the "
                "provided ball-designator pin strings - never invent pins, never use "
                "integer indices, never index by pin name. No markdown, no prose."),
        messages=[{"role": "user", "content": prompt}],
    )
    code = response.content[0].text
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    print("=== Generated SKiDL ===")
    print(code)
    with open(OUTPUT_PY, "w") as f:
        f.write(code)
    print(f"\nSaved to {OUTPUT_PY}")

    it, ot = response.usage.input_tokens, response.usage.output_tokens
    cost = it * 3.0 / 1_000_000 + ot * 15.0 / 1_000_000
    print(f"\n=== Tokens (SPI v2) ===\nInput: {it}  Output: {ot}  Cost: ${cost:.6f}")
    with open(TOKEN_LOG, "a") as f:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        f.write(f"{ts}\tv2\tmodel={MODEL}\tinput={it}\toutput={ot}\tcost=${cost:.6f}\n")


if __name__ == "__main__":
    generate()
