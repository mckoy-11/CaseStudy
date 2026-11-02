import json

import pytest
from fastapi import HTTPException

from api import main
from api import schemas


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    storage_path = tmp_path / "data.json"
    monkeypatch.setattr(main, "STORAGE_FILE", storage_path)
    collection_names = (
        "db_products",
        "db_batches",
        "db_inventory",
        "db_movements",
        "db_orders",
        "db_ingredients",
        "db_expenses",
        "db_events",
    )
    saved_collections = {
        name: dict(getattr(main, name))
        for name in collection_names
    }
    for name in collection_names:
        getattr(main, name).clear()

    try:
        yield storage_path
    finally:
        for name, saved_values in saved_collections.items():
            collection = getattr(main, name)
            collection.clear()
            collection.update(saved_values)


def test_api_uses_canonical_product_models() -> None:
    assert main.ProductCreate is schemas.ProductCreate
    assert main.ProductResponse is schemas.ProductResponse
    assert main.ProductUpdate is schemas.ProductUpdate


def test_product_crud_is_persisted_to_json(isolated_storage) -> None:
    product = schemas.ProductCreate(
        product_id="TEST-CHOC",
        name="Test Chocolate",
        unit_price=25,
    )
    created = main.create_product(product)
    assert created.name == "Test Chocolate"

    with pytest.raises(HTTPException) as duplicate:
        main.create_product(product)
    assert duplicate.value.status_code == 409

    assert any(row.product_id == "TEST-CHOC" for row in main.list_products())
    assert main.get_product("TEST-CHOC").name == "Test Chocolate"

    updated = main.update_product(
        "TEST-CHOC",
        schemas.ProductUpdate(name="Updated Chocolate", unit_price=30),
    )
    assert updated.name == "Updated Chocolate"

    main.deactivate_product("TEST-CHOC")
    with pytest.raises(HTTPException) as inactive_product:
        main.get_product("TEST-CHOC")
    assert inactive_product.value.status_code == 404
    assert all(row.product_id != "TEST-CHOC" for row in main.list_products())

    with isolated_storage.open("r", encoding="utf-8") as storage_file:
        persisted_json = json.load(storage_file)
    persisted_product = persisted_json["products"]["TEST-CHOC"]
    assert persisted_product["name"] == "Updated Chocolate"
    assert persisted_product["unit_price"] == 30
    assert persisted_product["active"] is False

    loaded = main.load_storage()
    assert loaded["products"]["TEST-CHOC"] == schemas.ProductResponse.model_validate(
        persisted_product
    )
