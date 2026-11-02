"""Main console navigation and dashboard."""

from __future__ import annotations

from typing import Any

from service import (
    APIClient,
    APIConnectionError,
    APIError,
    EventService,
    ExpenseService,
    InventoryService,
    IngredientService,
    OrderService,
    ProductService,
    ProductionService,
    ReportService,
)
from ui.inventory import InventoryScreen
from ui.events import EventScreen
from ui.expenses import ExpenseScreen
from ui.ingredients import IngredientScreen
from ui.orders import OrderScreen
from ui.products import ProductScreen
from ui.production import ProductionScreen
from ui.reports import ReportScreen
from utils.component import header, section, show_menu, show_table


class MainMenu:
    """Run the console UI and route screens through the shared API client."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()
        self.product_service = ProductService(self.client)
        self.production_service = ProductionService(self.client)
        self.ingredient_service = IngredientService(self.client)
        self.inventory_service = InventoryService(self.client)
        self.order_service = OrderService(self.client)
        self.report_service = ReportService(self.client)
        self.event_service = EventService(self.client)
        self.expense_service = ExpenseService(self.client)
        self.screens = {
            2: ProductScreen(self.product_service),
            3: IngredientScreen(self.ingredient_service),
            4: ProductionScreen(
                self.production_service, self.product_service, self.ingredient_service
            ),
            5: InventoryScreen(self.inventory_service, self.product_service),
            6: EventScreen(self.event_service, self.inventory_service),
            7: OrderScreen(self.order_service, self.product_service, self.event_service),
            8: ExpenseScreen(self.expense_service, self.production_service),
            9: ReportScreen(self.report_service),
        }

    def dashboard(self) -> dict[str, Any]:
        """Fetch and display the backend sales dashboard."""
        report = self.report_service.dashboard()
        section("Business Dashboard")
        sales_summary = report["sales_summary"]
        today_sales = report["sales_today"]
        cogs = sales_summary.get("estimated_cogs")
        profit = sales_summary.get("estimated_profit")
        show_table(
            ["Dashboard metric", "Value"],
            [
                ["Active products", report["total_products"]],
                ["Tracked ingredients", report["total_ingredients"]],
                ["Available finished stock", report["available_finished_stock"]],
                ["Low-stock products", len(report["low_stock_products"])],
                ["Low-stock ingredients", len(report["low_stock_ingredients"])],
                ["Production batches", report["production_batches"]],
                ["Pending reservations", report["pending_reservations"]],
                ["Open events", report["open_events"]],
                ["Completed orders", sales_summary["total_orders"]],
                ["Today's items sold", today_sales["total_items_sold"]],
                ["Today's sales", f"₱{today_sales['gross_revenue']:,.2f}"],
                ["Total completed sales", f"₱{sales_summary['gross_revenue']:,.2f}"],
                [
                    "Estimated production cost of sold items",
                    "Unavailable" if cogs is None else f"₱{cogs:,.2f}",
                ],
                [
                    "Recorded expenses",
                    f"₱{sales_summary.get('recorded_expenses', 0):,.2f}",
                ],
                [
                    "Estimated profit",
                    "Unavailable" if profit is None else f"₱{profit:,.2f}",
                ],
            ],
        )
        return report

    def run(self) -> None:
        """Run the top-level console menu until the user exits."""
        try:
            while True:
                header("Kakina Business Management System")
                choice = show_menu([
                    "[1] Dashboard",
                    "[2] Product catalog",
                    "[3] Ingredients and raw-material stock",
                    "[4] Production",
                    "[5] Finished-product inventory",
                    "[6] Booth events",
                    "[7] Orders, reservations, and sales",
                    "[8] Expenses",
                    "[9] Reports",
                    "[0] Exit",
                ])
                if choice in (0, None):
                    if choice is None:
                        print("Select a valid menu option.")
                        input("Press Enter to continue...")
                        continue
                    print("Goodbye.")
                    return

                try:
                    if choice == 1:
                        self.dashboard()
                    elif choice in self.screens:
                        self.screens[choice].run()
                    else:
                        print("Select a valid menu option.")
                except (APIError, APIConnectionError, ValueError) as exc:
                    print(f"\nError: {exc}")

                input("\nPress Enter to continue...")
        finally:
            self.client.close()
