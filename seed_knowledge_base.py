"""
seed_knowledge_base.py
Loads Ramayana passages from data/passages.json into ChromaDB.
Run this once before starting the app: python seed_knowledge_base.py
"""

import json
import os
import chromadb

# ── Config ──────────────────────────────────────────────────────────────────
DATA_FILE   = "data/passages.json"
DB_PATH     = "./ramayana_db"
COLLECTION  = "ramayana_passages"

def seed():
    # 1. Load passages
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found. Make sure you're in the project root.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        passages = json.load(f)
    print(f"Loaded {len(passages)} passages from {DATA_FILE}")

    # 2. Connect to ChromaDB (creates folder if it doesn't exist)
    client = chromadb.PersistentClient(path=DB_PATH)

    # 3. Delete existing collection if re-seeding
    existing = [c.name for c in client.list_collections()]
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
        print(f"Deleted existing collection: {COLLECTION}")

    # 4. Create fresh collection
    # ChromaDB uses its built-in onnxruntime embedder by default — no API key needed
    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for better semantic search
    )
    print(f"Created collection: {COLLECTION}")

    # 5. Add all passages
    collection.add(
        documents=[p["text"] for p in passages],
        metadatas=[
            {
                "kanda":      p["kanda"],
                "characters": ", ".join(p["characters"]),
                "topic":      p["topic"],
                "id":         p["id"]
            }
            for p in passages
        ],
        ids=[p["id"] for p in passages]
    )

    print(f"\nSuccessfully seeded {len(passages)} passages into ChromaDB!")
    print(f"   Database saved at: {DB_PATH}")
    print(f"\nYou can now run the app with: streamlit run app.py")

    # 6. Quick sanity check query
    print("\n── Sanity check query: 'Who is Hanuman?' ──")
    results = collection.query(query_texts=["Who is Hanuman?"], n_results=2)
    for doc in results["documents"][0]:
        print(f"  → {doc[:100]}...")


if __name__ == "__main__":
    seed()