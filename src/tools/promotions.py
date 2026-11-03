"""Active product promotion lookup."""

from __future__ import annotations

from typing import Any

from src.tools._shared import decimal_text, parse_id, store_data


def consultar_promocao(product_id: int | str) -> list[dict[str, Any]]:
    """Return only active promotions linked to the requested existing product.

    The discount is descriptive; this tool never computes a discounted price.
    An empty list means no active promotion was found in the available data.
    """
    identifier = parse_id(product_id)
    if identifier is None:
        return []
    data = store_data()
    if identifier not in data.products:
        return []
    return [
        {
            "promotion_id": promotion.promotion_id,
            "product_id": promotion.product_id,
            "discount_percent": decimal_text(promotion.discount_percent),
            "description": promotion.description,
        }
        for promotion in data.promotions
        if promotion.product_id == identifier and promotion.is_active
    ]
