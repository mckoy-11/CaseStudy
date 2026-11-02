"""Expense ledger operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class ExpenseService:
    """Create, search, update, and remove expense records."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def list_expenses(self, **filters: str) -> list[dict[str, Any]]:
        return self.client.get("/expenses", params=filters or None)

    def create_expense(self, expense: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("/expenses", json_body=expense)

    def update_expense(
        self, expense_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self.client.put(f"/expenses/{expense_id}", json_body=changes)

    def delete_expense(self, expense_id: str) -> None:
        self.client.delete(f"/expenses/{expense_id}")
