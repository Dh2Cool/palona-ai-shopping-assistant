"""
One-time script: pre-compute product embeddings using local sentence-transformers.

Run once from the backend/ directory:
    python precompute_embeddings.py

Output: data/product_embeddings.json  (commit this file to the repo)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Run: pip install sentence-transformers")
    sys.exit(1)

from app.catalog import load_catalog, get_searchable_text

MODEL_NAME = "all-MiniLM-L6-v2"
OUTPUT_PATH = Path(__file__).parent / "data" / "product_embeddings.json"


def main():
    print("Loading catalog...")
    catalog = load_catalog()
    print(f"  {len(catalog)} products loaded")

    print(f"Loading model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [get_searchable_text(p) for p in catalog]
    ids = [p["id"] for p in catalog]

    print(f"Computing {len(texts)} embeddings...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    output = {pid: emb.tolist() for pid, emb in zip(ids, embeddings)}

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f)

    print(f"\nSaved {len(output)} embeddings → {OUTPUT_PATH}")
    print("Done! Commit data/product_embeddings.json to your repo.")


if __name__ == "__main__":
    main()
