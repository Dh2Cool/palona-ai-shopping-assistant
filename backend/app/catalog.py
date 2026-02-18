"""Product catalog loader and utilities."""

import csv
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
CATALOG_CSVS = [
    DATA_DIR / "amazon_100_products.csv",
    DATA_DIR / "amazon_clothing_products.csv",
]


def _parse_rating(rating_str: str) -> float | None:
    """Extract numeric rating from '3.9 out of 5 stars' or similar."""
    if not rating_str:
        return None
    match = re.search(r"(\d+\.?\d*)\s*out of 5", rating_str, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _parse_review_count(count_str: str) -> int | None:
    """Extract count from '(14,356)' or similar."""
    if not count_str:
        return None
    digits = re.sub(r"[^\d]", "", count_str)
    return int(digits) if digits else None


def _load_from_csv(path: Path) -> list[dict[str, Any]]:
    """Load and normalize products from a single Amazon CSV."""
    products: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            asin = (row.get("asin") or "").strip()
            name = (row.get("product_name") or "").strip()
            image_url = (row.get("image_url") or "").strip()
            if not asin or not name or not image_url:
                continue
            if row.get("error") and "No product found" in row.get("error", ""):
                continue

            rating = _parse_rating(row.get("rating_overall") or "")
            review_count = _parse_review_count(row.get("review_count") or "")
            price_str = (row.get("price") or "").strip()
            description = (row.get("description") or "").strip()
            specs = (row.get("specs_text") or "").strip()
            url = (row.get("url") or "").strip()
            reviews_raw = (row.get("reviews_json") or "").strip()
            category = (row.get("category") or "").strip()

            products.append({
                "id": asin,
                "name": name,
                "price": price_str or "—",
                "price_raw": price_str,
                "image_url": image_url,
                "description": description or name,
                "rating": rating,
                "review_count": review_count,
                "url": url,
                "specs_text": specs[:800] if specs else "",
                "reviews_json": reviews_raw[:2000] if reviews_raw and reviews_raw != "[]" else "",
                "category": category,
            })
    return products


def load_catalog() -> list[dict[str, Any]]:
    """Load product catalog from all CSV files (amazon_100 + amazon_clothing)."""
    seen_ids: set[str] = set()
    products: list[dict[str, Any]] = []
    for csv_path in CATALOG_CSVS:
        if not csv_path.exists():
            continue
        try:
            for p in _load_from_csv(csv_path):
                pid = p.get("id") or ""
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    products.append(p)
        except Exception:
            continue
    return products


def get_product_by_id(product_id: str, catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Get a product by ID from the catalog."""
    for p in catalog:
        if p.get("id") == product_id:
            return p
    return None


def get_searchable_text(product: dict[str, Any]) -> str:
    """Build searchable text from product fields for embeddings."""
    parts = [
        product.get("name", ""),
        product.get("description", ""),
        product.get("specs_text", ""),
        product.get("category", ""),
    ]
    return " ".join(str(p) for p in parts if p)
