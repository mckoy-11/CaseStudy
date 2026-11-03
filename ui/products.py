"""Console screens for the product catalog."""

from __future__ import annotations

from uuid import uuid4

from service.product_service import ProductService
from utils.component import ask_identifier, ask_int, ask_number, ask_text, display_records, show_menu


PRODUCT_FIELDS = (
    ("ID", "product_id"),
    ("Product", "name"),
    ("Price", "unit_price"),
    ("Reorder At", "reorder_level"),
    ("Category", "category"),
    ("Description", "description"),
)


class ProductScreen:
    """Provide product list and create screens."""

    def __init__(self, service: ProductService) -> None:
        self.service = service

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] View product catalog",
                "[2] Add product",
                "[3] Update product",
                "[4] Deactivate product",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.list_products()
            elif choice == 2:
                self.create_product()
            elif choice == 3:
                self.update_product()
            elif choice == 4:
                self.deactivate_product()
            else:
                print("Select a valid product option.")

    def list_products(self) -> list[dict]:
        products = self.service.list_products()
        display_records("Product Catalog", products, PRODUCT_FIELDS)
        return products

    def create_product(self) -> dict:
        product = {
            "product_id": ask_identifier("Product ID (blank for generated): ", required=False)
            or f"PROD-{uuid4().hex[:8].upper()}",
            "name": ask_text("Product name: ", max_length=160),
            "unit_price": ask_number("Selling price (PHP): ", minimum=0.01),
            "description": ask_text("Description (optional): ", required=False) or None,
            "category": ask_text("Category (optional): ", required=False) or None,
            "reorder_level": (
                ask_int("Low-stock warning level (blank for 10): ", minimum=0, allow_blank=True)
            ),
        }
        if product["reorder_level"] is None:
            product["reorder_level"] = 10
        created = self.service.create_product(product)
        print(f"Product {created['product_id']} created successfully.")
        return created

    def update_product(self) -> dict:
        product_id = ask_identifier("Product ID: ")
        changes = {}
        name = ask_text("New name (blank to keep): ", required=False)
        price = ask_number("New unit price (blank to keep): ", minimum=0.01, allow_blank=True)
        category = ask_text("New category (blank to keep): ", required=False)
        reorder_level = ask_int(
            "New low-stock level (blank to keep): ",
            minimum=0,
            allow_blank=True,
        )
        if name:
            changes["name"] = name
        if price is not None:
            changes["unit_price"] = price
        if category:
            changes["category"] = category
        if reorder_level is not None:
            changes["reorder_level"] = reorder_level
        if not changes:
            print("No changes entered.")
            return {}
        return self.service.update_product(product_id, changes)

    def deactivate_product(self) -> None:
        product_id = ask_identifier("Product ID to deactivate: ")
        if not any(item["product_id"] == product_id for item in self.service.list_products()):
            raise ValueError(f"Unknown active product ID: {product_id}")
        confirmation = ask_text("Type DEACTIVATE to confirm: ")
        if confirmation.casefold() != "deactivate":
            print("Product deactivation cancelled.")
            return
        self.service.deactivate_product(product_id)
        print(f"Product {product_id} deactivated; its historical records remain.")
