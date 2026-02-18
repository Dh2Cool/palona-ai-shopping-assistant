"""Retrieval engine for product search. Uses ChromaDB when available, else in-memory embeddings."""

import threading
from typing import Any

from .catalog import get_searchable_text

# Try ChromaDB first (may fail on Python 3.14+)
_use_chroma = False
_chroma_collection = None
_product_embeddings: list[list[float]] = []
_catalog_snapshot: list[dict[str, Any]] = []
_initialized = False
_init_lock = threading.Lock()


def _try_import_chroma():
    """Lazy import ChromaDB; return True if successful."""
    try:
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils import embedding_functions
        from pathlib import Path

        client = chromadb.PersistentClient(
            path=str(Path(__file__).parent.parent / "chroma_data"),
            settings=Settings(anonymized_telemetry=False),
        )
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        try:
            client.delete_collection("products")
        except Exception:
            pass
        coll = client.create_collection(
            name="products",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        return coll
    except Exception:
        return None


def _ensure_initialized(catalog: list[dict[str, Any]]) -> None:
    """Initialize retrieval on first use. Thread-safe."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        init_collection(catalog)
        _initialized = True


def init_collection(catalog: list[dict[str, Any]]) -> None:
    """Initialize retrieval: ChromaDB if available, else in-memory embeddings."""
    global _use_chroma, _chroma_collection, _product_embeddings, _catalog_snapshot
    _catalog_snapshot = catalog

    coll = _try_import_chroma()
    if coll is not None:
        _use_chroma = True
        _chroma_collection = coll
        ids, documents, metadatas = [], [], []
        for p in catalog:
            pid = p.get("id") or str(id(p))
            ids.append(pid)
            documents.append(get_searchable_text(p))
            metadatas.append({"product_id": pid})
        for i in range(0, len(ids), 50):
            _chroma_collection.add(
                ids=ids[i : i + 50],
                documents=documents[i : i + 50],
                metadatas=metadatas[i : i + 50],
            )
        return

    # Fallback: in-memory embeddings
    from .embeddings import compute_embeddings_batch

    _product_embeddings[:] = compute_embeddings_batch(
        [get_searchable_text(p) for p in catalog]
    )


def search_products(
    query: str,
    catalog: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Semantic search over products. Uses ChromaDB or in-memory fallback. Initializes lazily on first call."""
    _ensure_initialized(catalog)
    if _use_chroma and _chroma_collection is not None:
        return _search_chroma(query, catalog, top_k)
    return _search_memory(query, catalog, top_k)


def _search_chroma(
    query: str, catalog: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """ChromaDB-based search."""
    if not query or not query.strip():
        query = "clothing and accessories"
    results = _chroma_collection.query(
        query_texts=[query],
        n_results=min(top_k * 2, _chroma_collection.count()),
        include=["distances", "metadatas"],
    )
    product_by_id = {p.get("id"): p for p in catalog if p.get("id")}
    out = []
    ids_seen = results.get("ids", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []
    metadatas_list = results.get("metadatas", [[]])[0] or []
    for i, pid in enumerate(ids_seen):
        if len(out) >= top_k:
            break
        dist = distances[i] if i < len(distances) else 0
        if dist > 0.65:  # cosine: 1 - 0.35
            continue
        meta = metadatas_list[i] if i < len(metadatas_list) else {}
        p = product_by_id.get(meta.get("product_id") or pid)
        if p:
            out.append(p)
    return out[:top_k]


def _search_memory(
    query: str, catalog: list[dict[str, Any]], top_k: int
) -> list[dict[str, Any]]:
    """In-memory embeddings fallback."""
    from .embeddings import search_products as _emb_search

    return _emb_search(query, catalog, _product_embeddings, top_k=top_k)
