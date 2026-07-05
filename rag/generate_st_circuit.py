import os
import sys
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

CHROMA_DIR = os.path.expanduser("~/PCBSchemaGen/rag/chroma_db")
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
MODEL = "qwen2.5-coder:7b"

TASK_DESCRIPTION = """
Design an STM32F411CEU6 minimum viable circuit.
Input node: VDD_3V3. Output nodes: NRST, BOOT0.

Use Part("test", "STM32F411CEU6", footprint="test:STM32F411CEU6") for the MCU.

Connect these pins exactly:
- stm32[1] (VBAT) to VDD_3V3, add 100nF cap between VDD_3V3 and GND
- stm32[8] (NRST) to NRST net, add 100nF cap between NRST and GND
- stm32[9] (VDDA) to VDD_3V3, add 100nF cap between VDD_3V3 and GND
- stm32[13] (VSS) to GND
- stm32[14] (VDD) to VDD_3V3, add 100nF cap between VDD_3V3 and GND
- stm32[24] (BOOT0) to BOOT0 net, add 10k resistor between BOOT0 and GND
- stm32[47] (VDD) to VDD_3V3, add 100nF cap between VDD_3V3 and GND
- stm32[48] (VSS) to GND

Use only Part(), Net(), and += for connections. End with ERC().
"""

def query_rag(question, n_results=4):
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name="st_datasheets",
        embedding_function=embedding_fn
    )
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    return results["documents"][0]

def build_prompt():
    # Retrieve relevant datasheet chunks
    chunks_nrst = query_rag("NRST pin reset capacitor 100nF")
    chunks_boot = query_rag("BOOT0 pin pull down resistor flash boot")
    chunks_vdd = query_rag("VDD decoupling capacitor power supply")
    chunks_crystal = query_rag("HSE crystal oscillator 8MHz load capacitor")

    context = "\n\n".join([
        "=== NRST Pin Info ===",
        chunks_nrst[0],
        "=== BOOT0 Pin Info ===",
        chunks_boot[0],
        "=== VDD Power Supply Info ===",
        chunks_vdd[0],
        "=== Crystal Oscillator Info ===",
        chunks_crystal[0],
    ])

    prompt = f"""You are a SKiDL Python code generator for STM32 circuits.

Here is relevant information from the STM32F411CE datasheet:
{context}

Task:
{TASK_DESCRIPTION}

Generate complete SKiDL Python code for this circuit.
Use ONLY these SKiDL patterns:
- Parts: Part("test", "R", value="10k", footprint="test:R_0805")
- Nets: Net("VDD_3V3")
- Connections: net += part[pin_number]
- End with: ERC()

For the STM32F411CEU6 use: Part("test", "STM32F411CEU6", footprint="test:STM32F411CEU6")
For crystal use: Part("test", "Crystal", footprint="test:Crystal_SMD_3225")

NEVER use Resistor(), Capacitor(), or .connect()
Start with: from skidl import *
End with: ERC()
"""
    return prompt

def generate_circuit():
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        timeout=600.0
    )

    prompt = build_prompt()
    print("Sending RAG-augmented prompt to LLM...")
    print(f"Prompt length: {len(prompt)} characters")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a SKiDL Python code generator. Output only valid Python code starting with from skidl import * and ending with ERC(). No explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=2048,
        timeout=300,
        temperature=0.3,
        extra_body={"think": False}
    )

    msg = response.choices[0].message
    code = msg.content
    if not code or code.strip() == "":
        code = getattr(msg, "reasoning", "") or ""
    print(f"Content length: {len(msg.content or '')}, Reasoning length: {len(getattr(msg, 'reasoning', '') or '')}")
    print("\n=== Raw Model Response ===")
    print(repr(code[:500]))
    print("\n=== Generated SKiDL Code ===")
    print(code)

    # Save to file
    output_path = os.path.expanduser("~/PCBSchemaGen/rag/stm32_mvc.py")
    # Extract just the Python code block
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    with open(output_path, "w") as f:
        f.write(code)
    print(f"\nCode saved to {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        TASK_DESCRIPTION = " ".join(sys.argv[1:])
        print(f"Using custom task: {TASK_DESCRIPTION[:100]}...")
    generate_circuit()
