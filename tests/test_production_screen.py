from ui.production import ProductionScreen


class FakeProductionService:
    def __init__(self) -> None:
        self.payload = None

    def record_batch(self, payload: dict) -> dict:
        self.payload = payload
        return {
            **payload,
            "total_batch_cost": 12,
            "unit_production_cost": 2,
        }


class FakeProductService:
    def list_products(self) -> list[dict]:
        return [{"product_id": "PROD-1", "name": "Chocolate", "unit_price": 6}]


def test_record_batch_does_not_require_ingredient_or_recipe_input(monkeypatch) -> None:
    production = FakeProductionService()
    screen = ProductionScreen(production, FakeProductService())
    prompts = iter(("PROD-1",))
    amounts = iter((6, 2, 4, 2))

    monkeypatch.setattr("ui.production.ask_text", lambda _prompt: next(prompts))
    monkeypatch.setattr(
        "ui.production.ask_number",
        lambda _prompt, **_kwargs: next(amounts),
    )
    monkeypatch.setattr("ui.production.display_records", lambda *_args: None)

    result = screen.record_batch()

    assert production.payload is not None
    assert production.payload["product_id"] == "PROD-1"
    assert production.payload["quantity_produced"] == 6
    assert production.payload["ingredients_used"] == []
    assert production.payload["packaging_cost"] == 2
    assert production.payload["labor_cost"] == 4
    assert production.payload["other_cost"] == 2
    assert result["total_batch_cost"] == 12
