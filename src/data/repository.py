"""Central UTF-8 loader and schema/relationship validation for CSV data."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config.settings import CSV_ENCODING, RAW_DATA_DIR
from src.data.exceptions import DataValidationError


@dataclass(frozen=True)
class Category:
    category_id: int
    name: str
    description: str


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    phone: str
    email: str
    city: str


@dataclass(frozen=True)
class Product:
    product_id: int
    price_brl: Decimal
    name: str
    category_id: int
    description: str
    stock_quantity: int
    status: str
    specs: dict[str, Any]
    created_at: date


@dataclass(frozen=True)
class Promotion:
    promotion_id: int
    product_id: int
    discount_percent: Decimal
    description: str
    is_active: bool


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    order_date: date
    status: str
    total_brl: Decimal
    payment_method: str
    tracking_code: str | None
    estimated_delivery: date | None
    notes: str | None


@dataclass(frozen=True)
class OrderItem:
    order_id: int
    quantity: int
    product_id: int


@dataclass(frozen=True)
class StoreData:
    categories: dict[int, Category]
    customers: dict[int, Customer]
    products: dict[int, Product]
    promotions: tuple[Promotion, ...]
    orders: dict[int, Order]
    order_items: tuple[OrderItem, ...]


_EXPECTED_COLUMNS = {
    "categories.csv": {"category_id", "name", "description"},
    "customers.csv": {"customer_id", "name", "phone", "email", "city"},
    "order_items.csv": {"order_id", "quantity", "product_id"},
    "orders.csv": {
        "order_id", "customer_id", "order_date", "status", "total_brl",
        "payment_method", "tracking_code", "estimated_delivery", "notes",
    },
    "products.csv": {
        "product_id", "price_brl", "name", "category_id", "description",
        "stock_quantity", "status", "specs", "created_at",
    },
    "promotions.csv": {
        "promotion_id", "product_id", "discount_percent", "description", "is_active",
    },
}


def _read_rows(directory: Path, filename: str) -> list[dict[str, str]]:
    path = directory / filename
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de dados obrigatório não encontrado: {path}")
    try:
        with path.open("r", encoding=CSV_ENCODING, newline="") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames
            if columns is None:
                raise DataValidationError(f"{filename}: cabeçalho CSV ausente.")
            if len(columns) != len(set(columns)):
                raise DataValidationError(f"{filename}: cabeçalho contém colunas duplicadas.")
            missing = _EXPECTED_COLUMNS[filename] - set(columns)
            if missing:
                raise DataValidationError(
                    f"{filename}: colunas obrigatórias ausentes: {', '.join(sorted(missing))}."
                )
            rows = []
            for row_number, row in enumerate(reader, start=2):
                if None in row:
                    raise DataValidationError(
                        f"{filename}, linha {row_number}: quantidade de campos não corresponde ao cabeçalho."
                    )
                rows.append(row)
            return rows
    except UnicodeDecodeError as error:
        raise DataValidationError(f"{filename}: arquivo não pôde ser lido como UTF-8.") from error


def _text(row: dict[str, str], field: str, filename: str, row_number: int) -> str:
    value = row.get(field)
    if value is None or not value.strip():
        raise DataValidationError(
            f"{filename}, linha {row_number}: campo obrigatório '{field}' vazio."
        )
    return value.strip()


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row.get(field)
    return value.strip() if value is not None and value.strip() else None


def _integer(
    row: dict[str, str], field: str, filename: str, row_number: int, *, minimum: int | None = None
) -> int:
    value = _text(row, field, filename, row_number)
    try:
        parsed = int(value)
    except ValueError as error:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve ser inteiro."
        ) from error
    if minimum is not None and parsed < minimum:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve ser >= {minimum}."
        )
    return parsed


def _decimal(
    row: dict[str, str], field: str, filename: str, row_number: int, *, minimum: Decimal | None = None,
    maximum: Decimal | None = None,
) -> Decimal:
    value = _text(row, field, filename, row_number)
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve ser número decimal."
        ) from error
    if not parsed.is_finite():
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve ser finito."
        )
    if minimum is not None and parsed < minimum:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve ser >= {minimum}."
        )
    if maximum is not None and parsed > maximum:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve ser <= {maximum}."
        )
    return parsed


def _date(row: dict[str, str], field: str, filename: str, row_number: int) -> date:
    value = _text(row, field, filename, row_number)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve usar a data ISO YYYY-MM-DD."
        ) from error


def _optional_date(row: dict[str, str], field: str, filename: str, row_number: int) -> date | None:
    value = _optional_text(row, field)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise DataValidationError(
            f"{filename}, linha {row_number}: '{field}' deve usar a data ISO YYYY-MM-DD."
        ) from error


def _unique_map(rows: list[Any], key: str, filename: str) -> dict[int, Any]:
    result: dict[int, Any] = {}
    for record in rows:
        identifier = getattr(record, key)
        if identifier in result:
            raise DataValidationError(f"{filename}: identificador duplicado '{identifier}'.")
        result[identifier] = record
    return result


def _validate_references(data: StoreData) -> None:
    for product in data.products.values():
        if product.category_id not in data.categories:
            raise DataValidationError(
                f"products.csv: produto {product.product_id} referencia categoria inexistente {product.category_id}."
            )
    for order in data.orders.values():
        if order.customer_id not in data.customers:
            raise DataValidationError(
                f"orders.csv: pedido {order.order_id} referencia cliente inexistente {order.customer_id}."
            )
    for item in data.order_items:
        if item.order_id not in data.orders:
            raise DataValidationError(
                f"order_items.csv: item referencia pedido inexistente {item.order_id}."
            )
        if item.product_id not in data.products:
            raise DataValidationError(
                f"order_items.csv: pedido {item.order_id} referencia produto inexistente {item.product_id}."
            )
    for promotion in data.promotions:
        if promotion.product_id not in data.products:
            raise DataValidationError(
                f"promotions.csv: promoção {promotion.promotion_id} referencia produto inexistente {promotion.product_id}."
            )


def _load_data(directory: Path) -> StoreData:
    categories = []
    for number, row in enumerate(_read_rows(directory, "categories.csv"), start=2):
        categories.append(Category(
            category_id=_integer(row, "category_id", "categories.csv", number, minimum=1),
            name=_text(row, "name", "categories.csv", number),
            description=_text(row, "description", "categories.csv", number),
        ))

    customers = []
    for number, row in enumerate(_read_rows(directory, "customers.csv"), start=2):
        customers.append(Customer(
            customer_id=_integer(row, "customer_id", "customers.csv", number, minimum=1),
            name=_text(row, "name", "customers.csv", number),
            phone=_text(row, "phone", "customers.csv", number),
            email=_text(row, "email", "customers.csv", number),
            city=_text(row, "city", "customers.csv", number),
        ))

    products = []
    for number, row in enumerate(_read_rows(directory, "products.csv"), start=2):
        specs_raw = _text(row, "specs", "products.csv", number)
        try:
            specs = json.loads(specs_raw)
        except json.JSONDecodeError as error:
            raise DataValidationError(f"products.csv, linha {number}: 'specs' deve conter JSON válido.") from error
        if not isinstance(specs, dict):
            raise DataValidationError(f"products.csv, linha {number}: 'specs' deve ser um objeto JSON.")
        products.append(Product(
            product_id=_integer(row, "product_id", "products.csv", number, minimum=1),
            price_brl=_decimal(row, "price_brl", "products.csv", number, minimum=Decimal("0")),
            name=_text(row, "name", "products.csv", number),
            category_id=_integer(row, "category_id", "products.csv", number, minimum=1),
            description=_text(row, "description", "products.csv", number),
            stock_quantity=_integer(row, "stock_quantity", "products.csv", number, minimum=0),
            status=_text(row, "status", "products.csv", number).casefold(),
            specs=specs,
            created_at=_date(row, "created_at", "products.csv", number),
        ))

    promotions = []
    for number, row in enumerate(_read_rows(directory, "promotions.csv"), start=2):
        active_raw = _text(row, "is_active", "promotions.csv", number).casefold()
        if active_raw not in {"1", "0", "true", "false"}:
            raise DataValidationError(
                f"promotions.csv, linha {number}: 'is_active' deve ser 0/1 ou true/false."
            )
        promotions.append(Promotion(
            promotion_id=_integer(row, "promotion_id", "promotions.csv", number, minimum=1),
            product_id=_integer(row, "product_id", "promotions.csv", number, minimum=1),
            discount_percent=_decimal(
                row, "discount_percent", "promotions.csv", number,
                minimum=Decimal("0"), maximum=Decimal("100"),
            ),
            description=_text(row, "description", "promotions.csv", number),
            is_active=active_raw in {"1", "true"},
        ))

    orders = []
    for number, row in enumerate(_read_rows(directory, "orders.csv"), start=2):
        orders.append(Order(
            order_id=_integer(row, "order_id", "orders.csv", number, minimum=1),
            customer_id=_integer(row, "customer_id", "orders.csv", number, minimum=1),
            order_date=_date(row, "order_date", "orders.csv", number),
            status=_text(row, "status", "orders.csv", number).casefold(),
            total_brl=_decimal(row, "total_brl", "orders.csv", number, minimum=Decimal("0")),
            payment_method=_text(row, "payment_method", "orders.csv", number),
            tracking_code=_optional_text(row, "tracking_code"),
            estimated_delivery=_optional_date(row, "estimated_delivery", "orders.csv", number),
            notes=_optional_text(row, "notes"),
        ))

    order_items = []
    for number, row in enumerate(_read_rows(directory, "order_items.csv"), start=2):
        order_items.append(OrderItem(
            order_id=_integer(row, "order_id", "order_items.csv", number, minimum=1),
            quantity=_integer(row, "quantity", "order_items.csv", number, minimum=1),
            product_id=_integer(row, "product_id", "order_items.csv", number, minimum=1),
        ))

    data = StoreData(
        categories=_unique_map(categories, "category_id", "categories.csv"),
        customers=_unique_map(customers, "customer_id", "customers.csv"),
        products=_unique_map(products, "product_id", "products.csv"),
        promotions=tuple(_unique_map(promotions, "promotion_id", "promotions.csv").values()),
        orders=_unique_map(orders, "order_id", "orders.csv"),
        order_items=tuple(order_items),
    )
    _validate_references(data)
    return data


@lru_cache(maxsize=4)
def _cached_load(directory: str) -> StoreData:
    return _load_data(Path(directory))


def load_store_data(directory: Path | str | None = None) -> StoreData:
    """Load all six CSVs once, validating schema, values, and foreign keys."""
    resolved = Path(directory or RAW_DATA_DIR).resolve()
    return _cached_load(str(resolved))
