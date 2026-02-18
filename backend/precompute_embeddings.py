"""
One-time script: pre-compute product embeddings using OpenAI and save to JSON.

Run once from the backend/ directory:
    python precompute_embeddings.py

Output: data/product_embeddings.json  (commit this file to the repo)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

from app.catalog import load_catalog, get_searchable_text

EMBED_MODEL = "text-embedding-3-small"
OUTPUT_PATH = Path(__file__).parent / "data" / "product_embeddings.json"
BATCH_SIZE = 100


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("Loading catalog...")
    catalog = load_catalog()
    print(f"  {len(catalog)} products loaded")

    texts = [get_searchable_text(p) for p in catalog]
    ids = [p["id"] for p in catalog]

    print(f"Computing embeddings with {EMBED_MODEL} (batches of {BATCH_SIZE})...")
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        all_embeddings.extend(batch_embeddings)
        print(f"  {min(i + BATCH_SIZE, len(texts))}/{len(texts)} done")

    output = {pid: emb for pid, emb in zip(ids, all_embeddings)}

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f)

    print(f"\nSaved {len(output)} embeddings to {OUTPUT_PATH}")
    print("Done! Commit data/product_embeddings.json to your repo.")


if __name__ == "__main__":
    main()
