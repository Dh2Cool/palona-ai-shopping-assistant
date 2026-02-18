"""Retrieval engine for product search using pre-computed OpenAI embeddings."""

from typing import Any

from .embeddings import search_products as _embedding_search


def is_ready() -> bool:
    """Always ready — no warm-up needed with pre-computed embeddings."""
    return True


def init_in_background(catalog: list[dict[str, Any]]) -> None:
    """No-op: embeddings are pre-computed and loaded from JSON instantly."""
    pass


def search_products(
    query: str,
    catalog: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Semantic search using pre-computed product embeddings + OpenAI query embedding."""
    return _embedding_search(query, catalog, top_k=top_k)
