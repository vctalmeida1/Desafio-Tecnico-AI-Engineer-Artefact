"""Minimal customer lookup by an exact customer identifier."""

from __future__ import annotations

import re
from typing import Any

from src.tools._shared import parse_id, store_data


def buscar_cliente(identificador: str | int) -> dict[str, Any] | None:
    """Find a customer by numeric ID, exact email, or normalized phone.

    Email and phone may be used as lookup keys but are never included in the result.
    """
    value = str(identificador).strip()
    if not value:
        return None
    data = store_data()

    customer = None
    numeric_id = parse_id(value)
    if numeric_id is not None:
        customer = data.customers.get(numeric_id)
    if customer is None:
        email = value.casefold()
        phone = re.sub(r"\D", "", value)
        customer = next(
            (
                candidate for candidate in data.customers.values()
                if candidate.email.casefold() == email
                or (phone and re.sub(r"\D", "", candidate.phone) == phone)
            ),
            None,
        )
    if customer is None:
        return None
    return {
        "customer_id": customer.customer_id,
        "name": customer.name,
        "city": customer.city,
    }
