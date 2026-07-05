import os
import chromadb
from chromadb.utils import embedding_functions
import anthropic

CHROMA_DIR = os.path.expanduser("~/PCBSchemaGen/rag/chroma_db")
MODEL = "claude-sonnet-4-6"

TASK_DESCRIPTION = """
Design a schematic to connect an STM32F401RET6 microcontroller with an ISM330DHCX
MEMS IMU sensor over I2C.

Input node: VDD_3V3
Output nodes: I2C_SCL, I2C_SDA

Requirements:
1. Use I2C1 on the STM32F401RET6:
   - SCL on PB6 (pin 58)
   - SDA on PB7 (pin 59)

2. STM32F401RET6 power connections:
   - All VDD pins (19, 32, 48, 64) to VDD_3V3 with 100nF decoupling caps
   - All VSS pins (18, 31, 47, 63) to GND
   - VBAT (pin 1) to VDD_3V3 with 100nF decoupling cap
   - VREF+ (pin 13) to VDD_3V3
   - VSSA (pin 12) to GND
   - VCAP1 (pin 30) to GND through 1uF capacitor
   - NRST (pin 7) to GND through 100nF capacitor
   - BOOT0 (pin 60) to GND through 10k resistor

3. ISM330DHCX connections:
   - VDD (pin 1) to VDD_3V3 with 100nF decoupling cap
   - VDDIO (pin 11) to VDD_3V3 with 100nF decoupling cap
   - GND pins (2, 10, 12, 14) all to GND
   - C1 (pin 3) to GND through 100nF capacitor
   - CS (pin 7) to VDD_3V3 through 10k resistor (I2C mode select)
   - SDO_SA0 (pin 5) to GND through 10k resistor (I2C address 0x6A)
   - SCL (pin 6) to I2C_SCL net
   - SDA (pin 4) to I2C_SDA net
   - INT1 (pin 8) and INT2 (pin 9) left unconnected using NC

4. I2C pull-up resistors:
   - 4.7k resistor from I2C_SCL to VDD_3V3
   - 4.7k resistor from I2C_SDA to VDD_3V3

5. Connect STM32 I2C pins to the shared I2C bus:
   - PB6 (pin 58) to I2C_SCL
   - PB7 (pin 59) to I2C_SDA

Use Part("test", "STM32F401RET6", footprint="test:STM32F401RET6") for the MCU.
Use Part("test", "ISM330DHCX", footprint="test:ISM330DHCX") for the sensor.
Use Part("test", "R", value="4k7", footprint="test:R_0805") for pull-up resistors.
Use Part("test", "R", value="10k", footprint="test:R_0805") for pull-down/config resistors.
Use Part("test", "C", value="100nF", footprint="test:C_0805") for decoupling caps.
Use Part("test", "C", value="1uF", footprint="test:C_0805") for VCAP1.
"""

def query_rag(question, n_results=3):
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name="st_datasheets",
        embedding_function=embedding_fn
    )
    results = collection.query(query_texts=[question], n_results=n_results)
    return results["documents"][0]

def build_prompt():
    chunks_i2c = query_rag("STM32F401 I2C1 PB6 PB7 SCL SDA alternate function")
    chunks_ism = query_rag("ISM330DHCX CS pin I2C mode SDO SA0 address VDD decoupling")
    chunks_vcap = query_rag("STM32F401 VCAP1 internal regulator capacitor")

    context = "\n\n".join([
        "=== STM32F401 I2C Pin Info ===",
        chunks_i2c[0],
        "=== ISM330DHCX I2C Configuration ===",
        chunks_ism[0],
        "=== STM32F401 VCAP1 Info ===",
        chunks_vcap[0],
    ])

    prompt = f"""You are a SKiDL Python code generator for STM32 and MEMS sensor circuits.

Relevant datasheet information:
{context}

Task:
{TASK_DESCRIPTION}

STRICT SKiDL RULES:
- Start with: from skidl import *
- Parts: Part("test", "PartName", footprint="test:FootprintName")
- Nets: Net("NET_NAME")
- Connections: net += part[pin_number]
- For unconnected pins: pin += NC
- End with: ERC()
- NEVER use Resistor(), Capacitor(), connect(), or any other syntax
- Use pin numbers only, not pin names
- Output ONLY the Python code, no explanations, no markdown formatting
"""
    return prompt, len(context)

def generate_circuit():
    client = anthropic.Anthropic()
    prompt, context_len = build_prompt()

    print(f"Sending RAG-augmented prompt to {MODEL}...")
    print(f"Context length: {context_len} characters")
    print(f"Prompt length: {len(prompt)} characters")

    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system="You are a SKiDL Python code generator. Output ONLY valid Python code. Start with from skidl import * and end with ERC(). Use ONLY Part(), Net(), and += for connections. No explanations, no markdown.",
        messages=[{"role": "user", "content": prompt}]
    )

    code = response.content[0].text

    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    print("\n=== Generated SKiDL Code (Claude) ===")
    print(code)

    output_path = os.path.expanduser("~/PCBSchemaGen/rag/stm32_ism330_i2c_claude.py")
    with open(output_path, "w") as f:
        f.write(code)

    print(f"\nCode saved to {output_path}")
    print(f"\n=== Token Usage ===")
    print(f"Input tokens:  {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")

    # Cost calculation (Claude Sonnet 4.6: $3/$15 per million tokens)
    input_cost = response.usage.input_tokens * 3.00 / 1_000_000
    output_cost = response.usage.output_tokens * 15.00 / 1_000_000
    total_cost = input_cost + output_cost
    print(f"Cost: ${total_cost:.6f}")

if __name__ == "__main__":
    generate_circuit()
