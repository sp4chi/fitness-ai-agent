"""
Ingests exercise-safety / injury-contraindication text documents into a
persistent Chroma vector store. Run once before using the Safety Check agent:

    python scripts/ingest_docs.py

Drop plain-text or markdown files into backend/data/safety_docs/ — one
"fact" or guideline per paragraph works best for retrieval quality.
"""
import os
import glob
import chromadb
from chromadb.utils import embedding_functions

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "safety_docs")
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) < max_chars:
            buffer += ("\n\n" if buffer else "") + p
        else:
            if buffer:
                chunks.append(buffer)
            buffer = p
    if buffer:
        chunks.append(buffer)
    return chunks


def main():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name="injury_safety_docs", embedding_function=embed_fn)

    files = glob.glob(os.path.join(DATA_DIR, "*.md")) + glob.glob(os.path.join(DATA_DIR, "*.txt"))
    if not files:
        print(f"No documents found in {DATA_DIR}. Add .md/.txt files and re-run.")
        return

    doc_id = 0
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_text(text)
        ids = [f"{os.path.basename(filepath)}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": os.path.basename(filepath)} for _ in chunks]
        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        doc_id += len(chunks)
        print(f"Ingested {len(chunks)} chunks from {filepath}")

    print(f"Done. Total chunks in collection: {collection.count()}")


if __name__ == "__main__":
    main()
