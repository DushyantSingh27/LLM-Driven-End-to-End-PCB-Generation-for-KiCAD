import os
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

DATASHEET_DIR = os.path.expanduser("~/PCBSchemaGen/datasheets")
CHROMA_DIR = os.path.expanduser("~/PCBSchemaGen/rag/chroma_db")

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def build_rag():
    os.makedirs(CHROMA_DIR, exist_ok=True)

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection("st_datasheets")
    except:
        pass

    collection = client.create_collection(
        name="st_datasheets",
        embedding_function=embedding_fn
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    all_chunks = []
    all_ids = []
    all_metadata = []

    for filename in os.listdir(DATASHEET_DIR):
        if not filename.endswith(".pdf"):
            continue

        pdf_path = os.path.join(DATASHEET_DIR, filename)
        component_name = filename.replace(".pdf", "").upper()

        print(f"Processing {filename}...")
        text = extract_text_from_pdf(pdf_path)
        chunks = splitter.split_text(text)
        print(f"  Generated {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{component_name}_chunk_{i}")
            all_metadata.append({
                "component": component_name,
                "source": filename,
                "chunk_index": i
            })

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            documents=all_chunks[i:i+batch_size],
            ids=all_ids[i:i+batch_size],
            metadatas=all_metadata[i:i+batch_size]
        )
        print(f"Indexed chunks {i} to {min(i+batch_size, len(all_chunks))}")

    print(f"\nRAG built successfully. Total chunks: {len(all_chunks)}")
    print(f"Stored in: {CHROMA_DIR}")

if __name__ == "__main__":
    build_rag()
