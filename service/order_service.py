"""Sales order operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class OrderService:
    """Create orders through the backend's sales endpoint."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def create_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Create an order using the API's SalesOrderCreate payload."""
        return self.client.post("/orders", json_body=order)

    def list_orders(
        self,
        status: str | None = None,
        location_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List orders with optional status/location filters."""
        params = {
            key: value for key, value in {
                "status_filter": status,
                "location_id": location_id,
            }.items() if value is not None
        }
        return self.client.get("/orders", params=params or None)

    def complete_reservation(self, order_id: str) -> dict[str, Any]:
        """Complete a pending reservation and deduct reserved inventory."""
        return self.client.post(f"/orders/{order_id}/complete")

    def cancel_reservation(self, order_id: str) -> dict[str, Any]:
        """Cancel a pending reservation and release reserved inventory."""
        return self.client.post(f"/orders/{order_id}/cancel")
