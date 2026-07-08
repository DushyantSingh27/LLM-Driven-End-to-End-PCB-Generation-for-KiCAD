"""
build_rag_v2.py -- upgraded RAG ingestion (pymupdf4llm markdown + table
preservation, markdown-aware chunking, new st_datasheets_v2 collection).
Original st_datasheets left intact as rollback. Metadata schema identical.
"""
import os
import pymupdf4llm
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter)
import chromadb
from chromadb.utils import embedding_functions

DATASHEET_DIR = os.path.expanduser("~/LLM_Driven_Schematic_Gen/datasheets")
CHROMA_DIR = os.path.expanduser("~/LLM_Driven_Schematic_Gen/rag/chroma_db")
COLLECTION = "st_datasheets_v2"
HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]
MAX_CHARS = 1200
OVERLAP = 120


def extract_markdown(pdf_path):
    return pymupdf4llm.to_markdown(pdf_path)


def chunk_markdown(md_text):
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS)
    sections = header_splitter.split_text(md_text)
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHARS, chunk_overlap=OVERLAP,
        separators=["\n\n", "\n", " ", ""])
    chunks = []
    for sec in sections:
        header_ctx = " > ".join(
            v for v in [sec.metadata.get("h1"), sec.metadata.get("h2"),
                        sec.metadata.get("h3")] if v)
        body = sec.page_content
        text = (f"[{header_ctx}]\n{body}" if header_ctx else body)
        if len(text) <= MAX_CHARS:
            chunks.append(text)
        else:
            for piece in char_splitter.split_text(body):
                chunks.append(
                    f"[{header_ctx}]\n{piece}" if header_ctx else piece)
    return chunks


def build():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION, embedding_function=embedding_fn)

    all_chunks, all_ids, all_metadata = [], [], []
    for filename in sorted(os.listdir(DATASHEET_DIR)):
        if not filename.endswith(".pdf"):
            continue
        pdf_path = os.path.join(DATASHEET_DIR, filename)
        component_name = filename.replace(".pdf", "").upper()
        print(f"Processing {filename} (pymupdf4llm markdown)...")
        md = extract_markdown(pdf_path)
        chunks = chunk_markdown(md)
        print(f"  {len(chunks)} chunks (markdown-aware)")
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{component_name}_chunk_{i}")
            all_metadata.append({
                "component": component_name, "source": filename,
                "chunk_index": i})

    batch = 100
    for i in range(0, len(all_chunks), batch):
        collection.add(
            documents=all_chunks[i:i + batch], ids=all_ids[i:i + batch],
            metadatas=all_metadata[i:i + batch])
        print(f"Indexed {i} to {min(i + batch, len(all_chunks))}")
    print(f"\nRAG v2 built. Total chunks: {len(all_chunks)}  Collection: {COLLECTION}")


if __name__ == "__main__":
    build()
