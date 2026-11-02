"""Sales and analytics report operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class ReportService:
    """Fetch sales reports from the backend."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def sales_summary(
        self,
        location_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Return a sales summary filtered by location or date range."""
        params = {
            key: value for key, value in {
                "location_id": location_id,
                "start_date": start_date,
                "end_date": end_date,
            }.items() if value is not None
        }
        return self.client.get("/reports/sales-summary", params=params or None)

    def dashboard(self) -> dict[str, Any]:
        """Return operational and sales dashboard metrics."""
        return self.client.get("/reports/dashboard")

    def low_stock(self) -> dict[str, Any]:
        """Return low-stock product and ingredient warnings."""
        return self.client.get("/reports/low-stock")

    def daily_sales(self, report_date: str) -> dict[str, Any]:
        """Return a daily sales summary."""
        return self.client.get("/reports/daily-sales", params={"report_date": report_date})

    def product_sales(self, **filters: str) -> list[dict[str, Any]]:
        """Return unit and revenue totals for products."""
        return self.client.get("/reports/product-sales", params=filters or None)

    def best_sellers(self, **filters: str) -> list[dict[str, Any]]:
        """Return product sales ranked by quantity sold."""
        return self.client.get("/reports/best-sellers", params=filters or None)

    def location_sales(self, **filters: str) -> list[dict[str, Any]]:
        """Return completed sales grouped by location."""
        return self.client.get("/reports/location-sales", params=filters or None)

    def production_costs(self, **filters: str) -> dict[str, Any]:
        """Return production batch and cost totals."""
        return self.client.get("/reports/production-costs", params=filters or None)

    def expenses(self, **filters: str) -> dict[str, Any]:
        """Return expenses grouped by category."""
        return self.client.get("/reports/expenses", params=filters or None)

    def financial_summary(self, **filters: str) -> dict[str, Any]:
        """Return sales, estimated cost of goods sold, expenses, and profit."""
        return self.client.get("/reports/financial-summary", params=filters or None)
