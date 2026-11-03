"""Protected order and order-item lookup tools."""

from __future__ import annotations

from typing import Any

from src.data.security import VerifiedCustomerContext, require_verified_customer
from src.tools._shared import decimal_text, parse_id, store_data


def consultar_pedido(
    order_id: int | str,
    *,
    identidade_verificada: VerifiedCustomerContext | None = None,
) -> dict[str, Any] | None:
    """Return an order only when trusted application code supplies verified identity.

    Create ``identidade_verificada`` only after validating the customer's identity.
    Unknown order and non-owned order both return None to avoid disclosing existence.
    """
    customer_id = require_verified_customer(identidade_verificada)
    identifier = parse_id(order_id)
    if identifier is None:
        return None
    order = store_data().orders.get(identifier)
    if order is None or order.customer_id != customer_id:
        return None
    return {
        "order_id": order.order_id,
        "status": order.status,
        "order_date": order.order_date.isoformat(),
        "total_brl": decimal_text(order.total_brl),
        "payment_method": order.payment_method,
        "tracking_code": order.tracking_code,
        "estimated_delivery": (
            order.estimated_delivery.isoformat() if order.estimated_delivery else None
        ),
    }


def consultar_itens_pedido(
    order_id: int | str,
    *,
    identidade_verificada: VerifiedCustomerContext | None = None,
) -> list[dict[str, Any]] | None:
    """Return item names and quantities for an order owned by verified customer.

    Returns None for an unknown or non-owned order, and [] when an accessible order
    has no item rows. Current catalogue prices are not used as historical prices.
    """
    customer_id = require_verified_customer(identidade_verificada)
    identifier = parse_id(order_id)
    if identifier is None:
        return None
    data = store_data()
    order = data.orders.get(identifier)
    if order is None or order.customer_id != customer_id:
        return None
    return [
        {
            "product_id": item.product_id,
            "product_name": data.products[item.product_id].name,
            "quantity": item.quantity,
        }
        for item in data.order_items
        if item.order_id == identifier
    ]
