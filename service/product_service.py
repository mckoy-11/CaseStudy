"""Product catalog operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class ProductService:
    """Call the backend product catalog endpoints."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def list_products(self) -> list[dict[str, Any]]:
        """Return all products from ``GET /products``."""
        return self.client.get("/products")

    def create_product(self, product: dict[str, Any]) -> dict[str, Any]:
        """Create a product using the API's ProductCreate payload."""
        return self.client.post("/products", json_body=product)

    def update_product(self, product_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        """Update selected catalog fields."""
        return self.client.patch(f"/products/{product_id}", json_body=changes)

    def deactivate_product(self, product_id: str) -> None:
        """Deactivate a product without deleting its historical records."""
        self.client.delete(f"/products/{product_id}")
