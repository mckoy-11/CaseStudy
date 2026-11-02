"""Production batch operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class ProductionService:
    """Create production batches through the backend."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def record_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Record a batch using the API's ProductionBatchCreate payload."""
        return self.client.post("/batches", json_body=batch)

    def list_batches(
        self,
        product_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """List batches, optionally filtering product and dates."""
        params = {
            key: value
            for key, value in {
                "product_id": product_id,
                "start_date": start_date,
                "end_date": end_date,
            }.items()
            if value is not None
        }
        return self.client.get("/batches", params=params or None)
