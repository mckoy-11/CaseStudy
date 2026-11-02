"""Console screens for API-backed sales reporting."""

from datetime import date

from service.report_service import ReportService
from utils.component import ask_text, section, show_menu, show_table


class ReportScreen:
    """Display overall or location-filtered sales summaries."""

    def __init__(self, reports: ReportService) -> None:
        self.reports = reports

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] Daily sales summary",
                "[2] Sales summary by date range/location",
                "[3] Best-selling products",
                "[4] Sales by product",
                "[5] Sales by location",
                "[6] Production costs",
                "[7] Expense summary",
                "[8] Estimated financial summary",
                "[9] Low-stock warnings",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.show_daily()
            elif choice == 2:
                self.show_range()
            elif choice == 3:
                self.show_best_sellers()
            elif choice == 4:
                self.show_product_sales()
            elif choice == 5:
                self.show_location_sales()
            elif choice == 6:
                self.show_production_costs()
            elif choice == 7:
                self.show_expenses()
            elif choice == 8:
                self.show_financial_summary()
            elif choice == 9:
                self.show_low_stock()
            else:
                print("Select a valid report option.")

    def show_summary(self, location_id: str | None = None) -> dict:
        report = self.reports.sales_summary(location_id)
        section("Sales Summary" + (f" - {location_id}" if location_id else ""))
        print(f"Completed orders: {report['total_orders']}")
        print(f"Items sold: {report['total_items_sold']}")
        print(f"Gross revenue: ₱{report['gross_revenue']:,.2f}")
        show_table(
            ["Channel", "Revenue"],
            [
                [channel, f"₱{amount:,.2f}"]
                for channel, amount in report["revenue_by_channel"].items()
            ],
        )
        return report

    def show_daily(self) -> dict:
        raw_date = ask_text(
            f"Report date YYYY-MM-DD (blank for {date.today().isoformat()}): ",
            required=False,
        )
        report_date = raw_date or date.today().isoformat()
        report = self.reports.daily_sales(report_date)
        section(f"Daily Sales - {report_date}")
        self._show_summary_fields(report)
        return report

    def show_range(self) -> dict:
        start_date, end_date = self._date_range()
        location_id = ask_text("Location ID filter (blank for all): ", required=False) or None
        report = self.reports.sales_summary(location_id, start_date, end_date)
        section("Sales Summary by Date and Location")
        self._show_summary_fields(report)
        return report

    def show_best_sellers(self) -> list[dict]:
        filters = self._date_filter_dict()
        location = ask_text("Location ID filter (blank for all): ", required=False)
        if location:
            filters["location_id"] = location
        rows = self.reports.best_sellers(**filters)
        show_table(
            ["Rank", "Product", "Quantity sold", "Revenue"],
            [
                [rank, row["product_name"], row["quantity_sold"], f"₱{row['revenue']:,.2f}"]
                for rank, row in enumerate(rows, 1)
            ],
        )
        return rows

    def show_product_sales(self) -> list[dict]:
        filters = self._date_filter_dict()
        location = ask_text("Location ID filter (blank for all): ", required=False)
        if location:
            filters["location_id"] = location
        rows = self.reports.product_sales(**filters)
        show_table(
            ["Product", "Quantity sold", "Revenue"],
            [[row["product_name"], row["quantity_sold"], f"₱{row['revenue']:,.2f}"] for row in rows],
        )
        return rows

    def show_location_sales(self) -> list[dict]:
        rows = self.reports.location_sales(**self._date_filter_dict())
        show_table(
            ["Location", "Orders", "Units sold", "Gross revenue"],
            [
                [
                    row.get("location_name") or row["location_id"],
                    row["total_orders"],
                    row["items_sold"],
                    f"₱{row['gross_revenue']:,.2f}",
                ]
                for row in rows
            ],
        )
        return rows

    def show_low_stock(self) -> dict:
        report = self.reports.low_stock()
        section("Low-stock Warnings")
        show_table(
            ["Product ID", "Product", "Available", "Reorder at"],
            [
                [
                    row["product_id"],
                    row["product_name"],
                    row["available_quantity"],
                    row["reorder_level"],
                ]
                for row in report["products"]
            ],
        )
        return report

    def show_production_costs(self) -> dict:
        start_date, end_date = self._date_range()
        filters = {key: value for key, value in {
            "start_date": start_date,
            "end_date": end_date,
        }.items() if value is not None}
        report = self.reports.production_costs(**filters)
        section("Production Cost Summary")
        print(f"Batches: {report['batch_count']}")
        print(f"Units produced: {report['units_produced']}")
        print(f"Total production cost: ₱{report['total_production_cost']:,.2f}")
        return report

    def show_expenses(self) -> dict:
        filters = self._date_filter_dict()
        report = self.reports.expenses(**filters)
        section("Expense Summary")
        print(f"Expense records: {report['expense_count']}")
        print(f"Total recorded expenses: ₱{report['total_expenses']:,.2f}")
        show_table(
            ["Category", "Amount"],
            [[category, f"₱{amount:,.2f}"] for category, amount in report["by_category"].items()],
        )
        return report

    def show_financial_summary(self) -> dict:
        report = self.reports.financial_summary(**self._date_filter_dict())
        section("Estimated Financial Summary")
        self._show_summary_fields(report)
        print(report["profit_note"])
        return report

    @staticmethod
    def _show_summary_fields(report: dict) -> None:
        print(f"Completed orders: {report['total_orders']}")
        print(f"Items sold: {report['total_items_sold']}")
        print(f"Gross revenue: ₱{report['gross_revenue']:,.2f}")
        cogs = report.get("estimated_cogs")
        print(f"Estimated cost of goods sold: {'Unavailable' if cogs is None else f'₱{cogs:,.2f}'}")
        print(f"Recorded expenses: ₱{report.get('recorded_expenses', 0):,.2f}")
        profit = report.get("estimated_profit")
        print(f"Estimated profit: {'Unavailable' if profit is None else f'₱{profit:,.2f}'}")
        show_table(
            ["Channel", "Revenue"],
            [
                [channel, f"₱{amount:,.2f}"]
                for channel, amount in report.get("revenue_by_channel", {}).items()
            ],
        )

    def _date_filter_dict(self) -> dict[str, str]:
        start_date, end_date = self._date_range()
        return {
            key: value for key, value in {
                "start_date": start_date,
                "end_date": end_date,
            }.items() if value is not None
        }

    @staticmethod
    def _date_range() -> tuple[str | None, str | None]:
        start_date = ask_text("Start date YYYY-MM-DD (blank for no lower bound): ", required=False) or None
        end_date = ask_text("End date YYYY-MM-DD (blank for no upper bound): ", required=False) or None
        try:
            parsed_start = date.fromisoformat(start_date) if start_date else None
            parsed_end = date.fromisoformat(end_date) if end_date else None
        except ValueError as exc:
            raise ValueError("Dates must use YYYY-MM-DD format.") from exc
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise ValueError("Start date must not be after end date.")
        return start_date, end_date
