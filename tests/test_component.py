from utils.component import ask_identifier
from ui.products import ProductScreen


def test_ask_identifier_normalizes_lowercase_input(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "prod-choc-1")

    assert ask_identifier("Product ID: ") == "PROD-CHOC-1"


def test_product_deactivation_accepts_lowercase_id_and_confirmation(monkeypatch) -> None:
    class FakeProductService:
        def __init__(self) -> None:
            self.deactivated_id: str | None = None

        def list_products(self) -> list[dict]:
            return [{"product_id": "PROD-1"}]

        def deactivate_product(self, product_id: str) -> None:
            self.deactivated_id = product_id

    responses = iter(("prod-1", "deactivate"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))
    service = FakeProductService()

    ProductScreen(service).deactivate_product()

    assert service.deactivated_id == "PROD-1"
