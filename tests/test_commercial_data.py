from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from src.data.exceptions import (
    DataValidationError,
    IdentityVerificationRequiredError,
)
from src.data.repository import load_store_data
from src.data.security import VerifiedCustomerContext
from src.tools import (
    buscar_cliente,
    buscar_produto,
    consultar_estoque,
    consultar_itens_pedido,
    consultar_pedido,
    consultar_promocao,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = PROJECT_ROOT / "data" / "raw"


class CommercialToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_store_data(RAW_DATA)

    def test_products_can_be_found_and_missing_products_are_empty(self) -> None:
        matches = buscar_produto(termo="violão")
        self.assertTrue(matches)
        self.assertTrue(any(product["category"] == "Violões" for product in matches))
        self.assertEqual(buscar_produto(nome="produto inexistente"), [])
        self.assertIsNone(consultar_estoque(999999))

    def test_search_by_category(self) -> None:
        matches = buscar_produto(categoria="Ukuleles")
        self.assertTrue(matches)
        self.assertTrue(all(product["category"] == "Ukuleles" for product in matches))

    def test_active_product_with_zero_stock_is_not_available(self) -> None:
        stock = consultar_estoque(96)
        self.assertIsNotNone(stock)
        self.assertEqual(stock["catalog_status"], "active")
        self.assertEqual(stock["commercial_status"], "out_of_stock")
        self.assertEqual(stock["quantity_available"], 0)
        self.assertFalse(stock["available"])

    def test_discontinued_product_is_not_sellable_even_with_physical_stock(self) -> None:
        stock = consultar_estoque(136)
        self.assertIsNotNone(stock)
        self.assertEqual(stock["catalog_status"], "discontinued")
        self.assertEqual(stock["quantity_available"], 0)
        self.assertFalse(stock["available"])

    def test_only_active_linked_promotions_are_returned(self) -> None:
        active = consultar_promocao(127)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["promotion_id"], 12)
        self.assertNotIn("promotional_price_brl", active[0])
        self.assertEqual(consultar_promocao(93), [])
        self.assertEqual(consultar_promocao(999999), [])

    def test_orders_require_verified_identity_and_hide_non_owned_orders(self) -> None:
        with self.assertRaises(IdentityVerificationRequiredError):
            consultar_pedido(1)
        with self.assertRaises(IdentityVerificationRequiredError):
            consultar_itens_pedido(1)

        owner_context = VerifiedCustomerContext._after_identity_verification(3)
        other_context = VerifiedCustomerContext._after_identity_verification(7)
        with self.assertRaises(AttributeError):
            owner_context.customer_id = 7
        order = consultar_pedido(1, identidade_verificada=owner_context)
        self.assertIsNotNone(order)
        self.assertEqual(order["order_id"], 1)
        self.assertEqual(order["status"], "delivered")
        self.assertIn("payment_method", order)
        self.assertIsNone(consultar_pedido(1, identidade_verificada=other_context))
        self.assertIsNone(consultar_pedido(999999, identidade_verificada=owner_context))

    def test_order_with_multiple_items_returns_all_quantities(self) -> None:
        verified_customer = VerifiedCustomerContext._after_identity_verification(18)
        items = consultar_itens_pedido(15, identidade_verificada=verified_customer)
        self.assertEqual(len(items), 2)
        self.assertTrue(all(item["quantity"] >= 1 for item in items))
        self.assertTrue(all("product_name" in item for item in items))

    def test_customer_lookup_does_not_return_full_contact_fields(self) -> None:
        customer = buscar_cliente(1)
        self.assertIsNotNone(customer)
        self.assertEqual(customer["customer_id"], 1)
        self.assertNotIn("phone", customer)
        self.assertNotIn("email", customer)
        source_customer = self.data.customers[1]
        self.assertEqual(buscar_cliente(source_customer.email)["customer_id"], 1)
        self.assertEqual(buscar_cliente(source_customer.phone)["customer_id"], 1)
        self.assertIsNone(buscar_cliente(999999))


class DataValidationTests(unittest.TestCase):
    def test_orphan_order_item_product_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            destination = Path(temp_directory)
            for path in RAW_DATA.glob("*.csv"):
                shutil.copy2(path, destination / path.name)

            items_path = destination / "order_items.csv"
            with items_path.open("r", encoding="utf-8", newline="") as file:
                rows = list(csv.DictReader(file))
                fieldnames = rows[0].keys()
            rows[0]["product_id"] = "999999"
            with items_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            with self.assertRaisesRegex(DataValidationError, "produto inexistente 999999"):
                load_store_data(destination)


if __name__ == "__main__":
    unittest.main()
