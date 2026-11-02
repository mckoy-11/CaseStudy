"""Console screens for sales orders."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from service.order_service import OrderService
from service.product_service import ProductService
from service.event_service import EventService
from utils.component import (
    ask_choice,
    ask_number,
    ask_text,
    display_records,
    show_menu,
)


CHANNELS = ("booth", "messenger", "direct_offering", "whatsapp", "facebook", "instagram", "walk_in", "online")
PAYMENT_METHODS = ("cash", "gcash", "bank_transfer")
FULFILLMENT_METHODS = ("pickup", "delivery", "walk_in")


class OrderScreen:
    """Create completed sales orders or pending reservations."""

    def __init__(
        self,
        orders: OrderService,
        products: ProductService,
        events: EventService | None = None,
    ) -> None:
        self.orders = orders
        self.products = products
        self.events = events

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] Record completed sale",
                "[2] Create reservation",
                "[3] View pending reservations",
                "[4] Complete reservation",
                "[5] Cancel reservation",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.create_order("completed")
            elif choice == 2:
                self.create_order("pending")
            elif choice == 3:
                self.list_reservations()
            elif choice == 4:
                self.transition_reservation("complete")
            elif choice == 5:
                self.transition_reservation("cancel")
            else:
                print("Select a valid order option.")

    def create_order(self, status: str) -> dict:
        products = self.products.list_products()
        display_records(
            "Product Catalog",
            products,
            (("ID", "product_id"), ("Product", "name"), ("Price", "unit_price")),
        )
        items_by_product: dict[str, int] = {}
        while True:
            product_id = ask_text("Product ID (blank when finished): ", required=False)
            if not product_id:
                break
            quantity = int(ask_number("Quantity: ", minimum=1))
            items_by_product[product_id] = items_by_product.get(product_id, 0) + quantity
        if not items_by_product:
            raise ValueError("Add at least one product to the order.")

        payload = {
            "order_id": f"ORD-{datetime.now():%Y%m%d}-{uuid4().hex[:6].upper()}",
            "channel": ask_choice("Order channel: ", CHANNELS),
            "location_id": self._select_location(),
            "customer_name": ask_text("Customer name: "),
            "messenger_account": ask_text("Messenger account (optional): ", required=False) or None,
            "contact_number": ask_text("Contact number (optional): ", required=False) or None,
            "items": [
                {"product_id": product_id, "quantity": quantity}
                for product_id, quantity in items_by_product.items()
            ],
            "delivery_fee": ask_number("Delivery fee (PHP, 0 if none): ", minimum=0),
            "payment_method": ask_choice("Payment method: ", PAYMENT_METHODS),
            "fulfillment": ask_choice("Fulfillment method: ", FULFILLMENT_METHODS),
            "status": status,
        }
        result = self.orders.create_order(payload)
        print(f"Order {result['order_id']} saved as {result['status']}.")
        print(f"Total amount: ₱{result['total_amount']:,.2f}")
        return result

    def _select_location(self) -> str:
        if self.events is not None:
            events = self.events.list_events(status="open")
            if events:
                display_records(
                    "Open selling events",
                    events,
                    (("Location ID", "location_id"), ("Event", "name"), ("Place", "location_name")),
                )
        return ask_text("Sales location ID (use LOC-CENTRAL for central direct sales): ")

    def list_reservations(self) -> list[dict]:
        orders = self.orders.list_orders(status="pending")
        display_records(
            "Pending Reservations",
            orders,
            (
                ("Order ID", "order_id"),
                ("Date", "timestamp"),
                ("Customer", "customer_name"),
                ("Location", "location_id"),
                ("Status", "status"),
                ("Total", "total_amount"),
                ("Items", "items"),
            ),
        )
        return orders

    def transition_reservation(self, action: str) -> dict:
        pending = self.orders.list_orders(status="pending")
        display_records(
            "Pending Reservations",
            pending,
            (("Order ID", "order_id"), ("Customer", "customer_name"), ("Location", "location_id"), ("Total", "total_amount")),
        )
        order_id = ask_text("Reservation/order ID: ")
        if not any(item["order_id"] == order_id for item in pending):
            raise ValueError(f"No pending reservation found with ID {order_id}.")
        result = (
            self.orders.complete_reservation(order_id)
            if action == "complete"
            else self.orders.cancel_reservation(order_id)
        )
        print(f"Reservation {order_id} is now {result['status']}.")
        return result
