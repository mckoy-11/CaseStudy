"""Inventory lookup and transfer operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class InventoryService:
    """Call backend endpoints for stock levels and transfers."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def get_stock_levels(self, location_id: str | None = None) -> list[dict[str, Any]]:
        """Get stock levels globally or filtered by location."""
        params = {"location_id": location_id} if location_id else None
        return self.client.get("/inventory/stock", params=params)

    def transfer_stock(self, transfer: dict[str, Any]) -> dict[str, Any]:
        """Transfer stock using the API's InventoryTransferCreate payload."""
        return self.client.post("/inventory/transfer", json_body=transfer)

    def adjust_stock(self, adjustment: dict[str, Any]) -> dict[str, Any]:
        """Reconcile counted quantity at one location."""
        return self.client.post("/inventory/adjustments", json_body=adjustment)

    def list_movements(
        self,
        location_id: str | None = None,
        product_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List stock movements, optionally filtered by location or product."""
        params = {
            key: value
            for key, value in {
                "location_id": location_id,
                "product_id": product_id,
            }.items()
            if value is not None
        }
        return self.client.get("/inventory/movements", params=params or None)
