"""Embeddings for semantic product search using OpenAI API."""

import json
import os
from pathlib import Path
from typing import Any

import numpy as np

EMBED_MODEL = "text-embedding-3-small"
RELEVANCE_THRESHOLD = 0.35

_EMBEDDINGS_PATH = Path(__file__).parent.parent / "data" / "product_embeddings.json"

# Loaded once at import time — just JSON parsing, instant
_product_embeddings_cache: dict[str, list[float]] | None = None


def _load_precomputed() -> dict[str, list[float]]:
    global _product_embeddings_cache
    if _product_embeddings_cache is None:
        if not _EMBEDDINGS_PATH.exists():
            raise FileNotFoundError(
                f"product_embeddings.json not found at {_EMBEDDINGS_PATH}. "
                "Run precompute_embeddings.py first."
            )
        with open(_EMBEDDINGS_PATH) as f:
            _product_embeddings_cache = json.load(f)
    return _product_embeddings_cache


def get_precomputed_embedding(product_id: str) -> list[float] | None:
    """Return the pre-computed embedding for a product ID, or None if missing."""
    return _load_precomputed().get(product_id)


def compute_embedding(text: str) -> list[float]:
    """Embed a query string using OpenAI API at runtime."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    va = np.array(a)
    vb = np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))


def search_products(
    query: str,
    catalog: list[dict[str, Any]],
    top_k: int = 5,
    min_score: float = RELEVANCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Semantic search: embed query via OpenAI, compare to pre-computed product embeddings."""
    precomputed = _load_precomputed()
    query_emb = compute_embedding(query)

    scored: list[tuple[float, dict[str, Any]]] = []
    for product in catalog:
        pid = product.get("id", "")
        emb = precomputed.get(pid)
        if emb is None:
            continue
        score = cosine_similarity(query_emb, emb)
        if score >= min_score:
            scored.append((score, product))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]
