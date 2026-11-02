"""Console screens for production batch recording."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from service.product_service import ProductService
from service.production_service import ProductionService
from utils.component import ask_number, ask_text, display_records, show_menu


class ProductionScreen:
    """Record finished-product output and batch-level production costs."""

    def __init__(
        self,
        production: ProductionService,
        products: ProductService,
    ) -> None:
        self.production = production
        self.products = products

    def run(self) -> None:
        choice = show_menu([
            "[1] Record production batch",
            "[2] View production history",
            "[0] Back",
        ])
        if choice == 1:
            self.record_batch()
        elif choice == 2:
            self.list_batches()
        elif choice != 0:
            print("Select a valid production option.")

    def record_batch(self) -> dict:
        product_list = self.products.list_products()
        display_records(
            "Products",
            product_list,
            (("ID", "product_id"), ("Product", "name"), ("Price", "unit_price")),
        )
        payload = {
            "batch_id": f"BATCH-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}",
            "product_id": ask_text("Product ID: "),
            "quantity_produced": int(ask_number("Quantity produced: ", minimum=1)),
            "ingredients_used": [],
            "packaging_cost": ask_number("Packaging cost for batch (PHP, 0 if none): ", minimum=0),
            "labor_cost": ask_number("Labor cost for batch (PHP, 0 if none): ", minimum=0),
            "other_cost": ask_number("Other production cost (PHP, 0 if none): ", minimum=0),
        }
        result = self.production.record_batch(payload)
        print(f"Production batch {result['batch_id']} recorded.")
        print(f"Total batch cost: ₱{result['total_batch_cost']:,.2f}")
        print(f"Unit production cost: ₱{result['unit_production_cost']:,.2f}")
        return result

    def list_batches(self) -> list[dict]:
        batches = self.production.list_batches()
        display_records(
            "Production History",
            batches,
            (
                ("Batch", "batch_id"),
                ("Date", "production_date"),
                ("Product ID", "product_id"),
                ("Quantity", "quantity_produced"),
                ("Batch Cost", "total_batch_cost"),
                ("Unit Cost", "unit_production_cost"),
            ),
        )
        return batches
