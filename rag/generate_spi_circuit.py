import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
import anthropic

CHROMA_DIR = os.path.expanduser("~/PCBSchemaGen/rag/chroma_db")
MODEL = "claude-sonnet-4-6"
OUTPUT_PY = os.path.expanduser("~/PCBSchemaGen/rag/lsm6dsm_stm32l476_spi.py")
TOKEN_LOG = os.path.expanduser("~/PCBSchemaGen/rag/spi_benchmark_tokens.txt")

# The EXACT user prompt - deliberately minimal. The model must do the engineering.
USER_TASK = (
    "LSM6DSM with STM32L476JGY6 interfaced over SPI. Used Interrupt pins "
    "as well and all the coupling and decoupling capacitors wherever necessary"
)

# Filtered RAG queries: (component_metadata_value, query_text)
RAG_QUERIES = [
    ("STM32L476JG", "SPI1 SCK MISO MOSI NSS alternate function pins ports"),
    ("STM32L476JG", "power supply VDD VDDA VCAP decoupling capacitor scheme"),
    ("STM32L476JG", "NRST BOOT0 reset boot configuration pins"),
    ("STM32L476JG", "VDDIO VREF VBAT power supply pins WLCSP72"),
    ("LSM6DSM", "SPI 4-wire interface SDI SDO SPC CS pin connection"),
    ("LSM6DSM", "INT1 INT2 interrupt pins output"),
    ("LSM6DSM", "VDD VDDIO decoupling capacitor power supply application"),
    ("LSM6DSM", "electrical connections mode SPI application hints"),
]


def get_collection():
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(name="st_datasheets", embedding_function=embedding_fn)


def build_rag_context(collection):
    """Run each filtered query, collect the top chunk per query, grouped by component."""
    sections = {"STM32L476JG": [], "LSM6DSM": []}
    for comp, query in RAG_QUERIES:
        res = collection.query(
            query_texts=[query],
            n_results=2,
            where={"component": comp}
        )
        for doc in res["documents"][0]:
            if doc not in sections[comp]:   # dedupe
                sections[comp].append(doc)

    parts = []
    parts.append("=== STM32L476JGY6 (WLCSP72) DATASHEET CONTEXT ===")
    parts.extend(sections["STM32L476JG"])
    parts.append("\n=== LSM6DSM DATASHEET CONTEXT ===")
    parts.extend(sections["LSM6DSM"])
    return "\n\n".join(parts)


def build_prompt(context):
    return f"""You are a SKiDL Python code generator for STM32 and MEMS sensor circuits.

You are given datasheet context for two parts. Use it, plus your own engineering
knowledge, to design a correct, hardware-complete circuit. You must decide the pin
assignments, the SPI wiring, the interrupt routing, and all passive component values
yourself - the task description is intentionally high-level.

Relevant datasheet information:
{context}

Task:
{USER_TASK}

DESIGN REQUIREMENTS (infer specifics yourself):
- Interface the two chips over a 4-wire SPI bus (SCLK, MOSI, MISO, CS).
- Route the sensor's two interrupt pins (INT1, INT2) to suitable STM32 GPIOs.
- Add all decoupling/coupling capacitors each datasheet recommends, on every
  power rail that needs them, with appropriate values.
- Handle mandatory STM32 support pins (NRST, BOOT0, VCAP, VREF, VDDA) correctly.
- Configure the LSM6DSM for SPI mode (not I2C).
- Choose standard, sensible passive values.

STRICT SKiDL RULES:
- Start with: from skidl import *
- Parts: Part("test", "PartName", footprint="test:FootprintName")
- Use Part("test", "STM32L476JGY6", footprint="test:STM32L476JGY6") for the MCU.
- Use Part("test", "LSM6DSM", footprint="test:LSM6DSM") for the sensor.
- Use Part("test", "R", value="<val>", footprint="test:R_0805") for resistors.
- Use Part("test", "C", value="<val>", footprint="test:C_0805") for capacitors.
- Nets: Net("NET_NAME")
- Connections: net += part[pin_number]
- For unconnected pins: part[pin_number] += NC
- End with: ERC()
- NEVER use Resistor(), Capacitor(), connect(), or any other syntax.
- Use pin numbers only, not pin names.
- Output ONLY the Python code, no explanations, no markdown formatting.
"""


def generate():
    collection = get_collection()
    context = build_rag_context(collection)
    prompt = build_prompt(context)

    print(f"Model: {MODEL}")
    print(f"RAG context length: {len(context)} chars")
    print(f"Full prompt length: {len(prompt)} chars")
    print("Generating BLIND (no ground-truth schematic provided)...\n")

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=(
            "You are a SKiDL Python code generator. Output ONLY valid Python code. "
            "Start with 'from skidl import *' and end with 'ERC()'. Use ONLY Part(), "
            "Net(), and += for connections. No explanations, no markdown."
        ),
        messages=[{"role": "user", "content": prompt}]
    )

    code = response.content[0].text
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    print("=== Generated SKiDL Code ===")
    print(code)

    with open(OUTPUT_PY, "w") as f:
        f.write(code)
    print(f"\nSaved to {OUTPUT_PY}")

    it = response.usage.input_tokens
    ot = response.usage.output_tokens
    cost = it * 3.00 / 1_000_000 + ot * 15.00 / 1_000_000

    print(f"\n=== Token Usage (SPI benchmark) ===")
    print(f"Input tokens:  {it}")
    print(f"Output tokens: {ot}")
    print(f"Cost: ${cost:.6f}")

    with open(TOKEN_LOG, "a") as f:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        f.write(f"{ts}\tmodel={MODEL}\tinput={it}\toutput={ot}\tcost=${cost:.6f}\n")
    print(f"Token usage appended to {TOKEN_LOG}")


if __name__ == "__main__":
    generate()
