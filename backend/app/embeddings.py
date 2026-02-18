"""Embeddings for semantic product search."""

from typing import Any

import numpy as np

# Lazy load to avoid slow startup when using Groq embeddings
_model = None


def _get_model():
    """Lazy load sentence-transformers model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def compute_embedding(text: str) -> list[float]:
    """Compute embedding for a single text."""
    model = _get_model()
    return model.encode(text, convert_to_numpy=True).tolist()


def compute_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Compute embeddings for multiple texts."""
    model = _get_model()
    return model.encode(texts, convert_to_numpy=True).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    va = np.array(a)
    vb = np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))


RELEVANCE_THRESHOLD = 0.35  # Min cosine similarity to be considered relevant


def search_products(
    query: str,
    catalog: list[dict[str, Any]],
    product_embeddings: list[list[float]],
    top_k: int = 5,
    min_score: float = RELEVANCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Semantic search over products. Returns top_k most similar products above min_score."""
    from .catalog import get_searchable_text

    query_emb = compute_embedding(query)
    scores = [
        cosine_similarity(query_emb, emb) for emb in product_embeddings
    ]
    indices = np.argsort(scores)[::-1]
    results = []
    for i in indices:
        if scores[i] < min_score:
            break
        results.append(catalog[i])
        if len(results) >= top_k:
            break
    return results
