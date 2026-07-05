import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = os.path.expanduser("~/PCBSchemaGen/rag/chroma_db")

def query_rag(question, n_results=5):
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

if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "NRST pin decoupling capacitor"
    print(f"Query: {question}\n")
    chunks = query_rag(question)
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(chunk[:400])
        print()
