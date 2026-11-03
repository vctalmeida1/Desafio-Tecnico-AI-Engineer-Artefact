"""Product search and stock availability tools."""

from __future__ import annotations

from typing import Any

from src.tools._shared import normalize_text, parse_id, product_to_dict, store_data


def buscar_produto(
    *, termo: str | None = None, nome: str | None = None,
    categoria: str | int | None = None, limite: int = 20,
) -> list[dict[str, Any]]:
    """Search products by name, category, or free-text term.

    Multiple supplied filters are combined. Free text matches name, description,
    or category. An empty search is rejected instead of returning the catalogue.
    """
    if not any(value is not None and str(value).strip() for value in (termo, nome, categoria)):
        raise ValueError("Informe pelo menos um termo, nome ou categoria para a busca.")
    if not 1 <= limite <= 100:
        raise ValueError("limite deve estar entre 1 e 100.")

    data = store_data()
    term_filter = normalize_text(termo.strip()) if termo and termo.strip() else None
    name_filter = normalize_text(nome.strip()) if nome and nome.strip() else None
    category_filter = normalize_text(str(categoria).strip()) if categoria is not None and str(categoria).strip() else None
    results = []
    for product in data.products.values():
        category = data.categories[product.category_id]
        if name_filter and name_filter not in normalize_text(product.name):
            continue
        if category_filter and category_filter not in {
            normalize_text(category.name), str(category.category_id),
        } and category_filter not in normalize_text(category.name):
            continue
        if term_filter:
            searchable = " ".join((product.name, product.description, category.name))
            if term_filter not in normalize_text(searchable):
                continue
        results.append(product_to_dict(product, data))
        if len(results) >= limite:
            break
    return results


def consultar_estoque(product_id: int | str) -> dict[str, Any] | None:
    """Return sellable quantity and catalog status; active alone is insufficient."""
    identifier = parse_id(product_id)
    if identifier is None:
        return None
    product = store_data().products.get(identifier)
    if product is None:
        return None

    if product.status != "active":
        commercial_status = product.status
        quantity_available = 0
    elif product.stock_quantity <= 0:
        commercial_status = "out_of_stock"
        quantity_available = 0
    else:
        commercial_status = "available"
        quantity_available = product.stock_quantity
    return {
        "product_id": product.product_id,
        "name": product.name,
        "quantity_available": quantity_available,
        "commercial_status": commercial_status,
        "catalog_status": product.status,
        "available": quantity_available > 0,
    }
