import chromadb
import os

from chunking import load_document, chunk_by_structure, DATA_FILE
from embedder import embed

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "handbook"


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,  # we bring our own Gemini embeddings
        configuration={"hnsw": {"space": "cosine"}},
    )


def ingest():
    # 1. LOAD the document
    doc = load_document()
    source = os.path.basename(DATA_FILE)
    print(f"1. Loaded '{source}' ({len(doc)} chars)")

    # 2. CHUNK it
    chunks = chunk_by_structure(doc)
    print(f"2. Split into {len(chunks)} chunks")

    # 3. EMBED every chunk (one API call for all of them)
    texts = [c["text"] for c in chunks]
    vectors = embed(texts, task_type="RETRIEVAL_DOCUMENT")
    print(f"3. Embedded {len(vectors)} chunks -> {len(vectors[0])} numbers each")

    # 4. STORE in ChromaDB
    # upsert = insert, or overwrite if the id already exists.
    # Stable ids ("handbook.md-0", ...) mean re-running never creates duplicates.
    collection = get_collection()
    collection.upsert(
        ids=[f"{source}-{i}" for i in range(len(chunks))],
        documents=texts,
        embeddings=vectors,
        metadatas=[
            {"source": source, "section": c["section"], "chunk_index": i}
            for i, c in enumerate(chunks)
        ],
    )
    print(f"4. Stored in collection '{COLLECTION_NAME}' -> {collection.count()} items total")
    return collection


if __name__ == "__main__":
    collection = ingest()

    # Peek inside the database to confirm what was saved
    print("\n=== WHAT'S IN THE DATABASE ===")
    stored = collection.get(include=["documents", "metadatas", "embeddings"], limit=3)
    for id_, doc, meta, vec in zip(
        stored["ids"], stored["documents"], stored["metadatas"], stored["embeddings"]
    ):
        print(f"\nid:        {id_}")
        print(f"metadata:  {meta}")
        print(f"embedding: [{', '.join(f'{v:.4f}' for v in vec[:4])}, ...] ({len(vec)} numbers)")
        print(f"text:      {doc[:90]}...")
