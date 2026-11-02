"""Ingredient inventory operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class IngredientService:
    """Create and adjust tracked ingredient inventory."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def list_ingredients(self) -> list[dict[str, Any]]:
        return self.client.get("/ingredients")

    def create_ingredient(self, ingredient: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("/ingredients", json_body=ingredient)

    def update_ingredient(
        self, ingredient_id: str, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self.client.patch(f"/ingredients/{ingredient_id}", json_body=changes)

    def adjust_stock(
        self, ingredient_id: str, adjustment: dict[str, Any]
    ) -> dict[str, Any]:
        return self.client.post(
            f"/ingredients/{ingredient_id}/adjustments",
            json_body=adjustment,
        )
