"""Console screens for inventory viewing and transfers."""

from __future__ import annotations

from uuid import uuid4

from service.inventory_service import InventoryService
from service.product_service import ProductService
from utils.component import ask_identifier, ask_int, ask_text, display_records, show_menu


class InventoryScreen:
    """View location stock and transfer stock between locations."""

    def __init__(self, inventory: InventoryService, products: ProductService) -> None:
        self.inventory = inventory
        self.products = products

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] View stock at all locations",
                "[2] View stock at one location",
                "[3] Transfer stock",
                "[4] Reconcile a physical stock count",
                "[5] View stock movement history",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.list_stock()
            elif choice == 2:
                self.list_stock(ask_identifier("Location ID: "))
            elif choice == 3:
                self.transfer_stock()
            elif choice == 4:
                self.reconcile_stock()
            elif choice == 5:
                self.movement_history()
            else:
                print("Select a valid inventory option.")

    def list_stock(self, location_id: str | None = None) -> list[dict]:
        stock = self.inventory.get_stock_levels(location_id)
        display_records(
            "Inventory Stock",
            stock,
            (
                ("Location", "location_id"),
                ("Product ID", "product_id"),
                ("Product", "product_name"),
                ("Available", "quantity_available"),
            ),
        )
        return stock

    def transfer_stock(self) -> dict:
        products = self.products.list_products()
        display_records(
            "Products",
            products,
            (("ID", "product_id"), ("Product", "name"), ("Price", "unit_price")),
        )
        source = ask_identifier("Source location ID: ")
        destination = ask_identifier("Destination location ID: ")
        if source == destination:
            raise ValueError("Source and destination locations must be different.")
        payload = {
            "movement_id": f"MOV-{uuid4().hex[:12].upper()}",
            "source_location_id": source,
            "destination_location_id": destination,
            "product_id": ask_identifier("Product ID: "),
            "quantity": ask_int("Quantity to transfer: ", minimum=1),
        }
        result = self.inventory.transfer_stock(payload)
        print(f"Transferred {result['quantity']} unit(s) to {result['destination_location_id']}.")
        return result

    def reconcile_stock(self) -> dict:
        location_id = ask_identifier("Location ID: ")
        stock = self.inventory.get_stock_levels(location_id)
        if stock:
            display_records(
                "Current stock at location",
                stock,
                (("Product ID", "product_id"), ("Product", "product_name"), ("On hand", "quantity_on_hand")),
            )
        product_id = ask_identifier("Product ID to count: ")
        if not any(item["product_id"] == product_id for item in self.products.list_products()):
            raise ValueError(f"Unknown product ID: {product_id}")
        current = next(
            (item["quantity_on_hand"] for item in stock if item["product_id"] == product_id),
            0,
        )
        counted = ask_int("Physically counted quantity: ", minimum=0)
        change = counted - current
        if change == 0:
            print("Count matches the system quantity; no adjustment is required.")
            return {"stock": current, "movement": None}
        result = self.inventory.adjust_stock({
            "location_id": location_id,
            "product_id": product_id,
            "quantity_change": change,
            "reason": ask_text("Count variance reason: "),
        })
        print(f"Stock reconciled: {current} → {counted}.")
        return result

    def movement_history(self) -> list[dict]:
        location_id = ask_identifier("Location ID filter (blank for all): ", required=False) or None
        product_id = ask_identifier("Product ID filter (blank for all): ", required=False) or None
        movements = self.inventory.list_movements(location_id, product_id)
        display_records(
            "Stock Movement History",
            movements,
            (
                ("Timestamp", "timestamp"),
                ("Movement", "movement_type"),
                ("Product ID", "product_id"),
                ("Quantity", "quantity"),
                ("From", "source_location_id"),
                ("To", "destination_location_id"),
                ("Reason", "reason"),
            ),
        )
        return movements
