"""Common serialization and lookup helpers for commercial tools."""

from __future__ import annotations

import unicodedata
from decimal import Decimal
from typing import Any

from src.data.repository import StoreData, load_store_data


def store_data() -> StoreData:
    return load_store_data()


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def decimal_text(value: Decimal) -> str:
    return format(value, "f")


def parse_id(value: int | str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def product_to_dict(product: Any, data: StoreData) -> dict[str, Any]:
    category = data.categories[product.category_id]
    return {
        "product_id": product.product_id,
        "name": product.name,
        "category": category.name,
        "description": product.description,
        "price_brl": decimal_text(product.price_brl),
        "catalog_status": product.status,
    }
