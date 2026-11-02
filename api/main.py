from datetime import date, datetime
from contextlib import asynccontextmanager
from enum import Enum
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, PositiveInt

Status = status


class ProductCreate(BaseModel):
    product_id: str
    name: str
    unit_price: float = Field(gt=0)
    description: Optional[str] = None
    category: Optional[str] = None
    packaging: Optional[str] = None
    weight_grams: Optional[float] = Field(default=None, gt=0)
    pieces_per_pack: Optional[int] = Field(default=None, gt=0)
    reorder_level: int = Field(default=10, ge=0)
    active: bool = True


class ProductResponse(ProductCreate):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    unit_price: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = None
    category: Optional[str] = None
    packaging: Optional[str] = None
    weight_grams: Optional[float] = Field(default=None, gt=0)
    pieces_per_pack: Optional[int] = Field(default=None, gt=0)
    reorder_level: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None


class IngredientUsage(BaseModel):
    ingredient_name: Optional[str] = None
    ingredient_id: Optional[str] = None
    quantity_used: float = Field(ge=0)
    cost_per_unit: Optional[float] = Field(default=None, ge=0)


class ProductionBatchCreate(BaseModel):
    batch_id: str
    product_id: str
    quantity_produced: PositiveInt
    ingredients_used: List[IngredientUsage]
    packaging_cost: float = Field(default=0, ge=0)
    labor_cost: float = Field(default=0, ge=0)
    other_cost: float = Field(default=0, ge=0)


class ProductionBatchResponse(ProductionBatchCreate):
    production_date: datetime
    total_batch_cost: float
    unit_production_cost: float


class IngredientCreate(BaseModel):
    ingredient_id: str
    name: str
    unit: str
    unit_cost: float = Field(ge=0)
    current_stock_qty: float = Field(ge=0)
    reorder_level: float = Field(default=0, ge=0)


class IngredientAdjustment(BaseModel):
    quantity_change: float
    reason: str = Field(min_length=1, max_length=300)


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = Field(default=None, ge=0)
    reorder_level: Optional[float] = Field(default=None, ge=0)
    active: Optional[bool] = None


class InventoryTransferCreate(BaseModel):
    movement_id: str
    source_location_id: str
    destination_location_id: str
    product_id: str
    quantity: PositiveInt


class InventoryTransferResponse(InventoryTransferCreate):
    timestamp: datetime
    movement_type: str = "transfer"
    reason: str = ""


class InventoryAdjustment(BaseModel):
    location_id: str
    product_id: str
    quantity_change: int
    reason: str = Field(min_length=1, max_length=300)


class EventCreate(BaseModel):
    event_id: str
    name: str
    location_name: str
    province: str = "Nueva Ecija"
    event_date: Optional[datetime] = None


class ExpenseCreate(BaseModel):
    expense_id: str
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    amount: float = Field(gt=0)
    expense_date: Optional[datetime] = None
    related_batch_id: Optional[str] = None
    location_id: Optional[str] = None


class ExpenseUpdate(BaseModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    amount: Optional[float] = Field(default=None, gt=0)
    expense_date: Optional[datetime] = None
    related_batch_id: Optional[str] = None
    location_id: Optional[str] = None


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: PositiveInt


class OrderItemResponse(OrderItemCreate):
    unit_price: float
    subtotal: float


class OrderChannel(str, Enum):
    BOOTH = "booth"
    MESSENGER = "messenger"
    DIRECT_OFFERING = "direct_offering"
    WHATSAPP = "whatsapp"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WALK_IN = "walk_in"
    ONLINE = "online"


class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReservationStatusUpdate(BaseModel):
    status: OrderStatus


class PaymentMethod(str, Enum):
    CASH = "cash"
    GCASH = "gcash"
    BANK_TRANSFER = "bank_transfer"


class FulfillmentMethod(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
    WALK_IN = "walk_in"


class SalesOrderCreate(BaseModel):
    order_id: str
    channel: OrderChannel
    location_id: str
    customer_name: str
    messenger_account: Optional[str] = None
    contact_number: Optional[str] = None
    items: List[OrderItemCreate] = Field(min_length=1)
    delivery_fee: float = 0.0
    payment_method: PaymentMethod
    fulfillment: FulfillmentMethod
    status: OrderStatus = OrderStatus.PENDING


class SalesOrderResponse(BaseModel):
    order_id: str
    channel: OrderChannel
    location_id: str
    customer_name: str
    messenger_account: Optional[str] = None
    contact_number: Optional[str] = None
    items: List[OrderItemResponse]
    delivery_fee: float = 0.0
    payment_method: PaymentMethod
    fulfillment: FulfillmentMethod
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime
    total_amount: float
    estimated_cogs: Optional[float] = None


class SalesSummaryResponse(BaseModel):
    total_orders: int
    gross_revenue: float
    total_items_sold: int
    revenue_by_channel: Dict[str, float] = Field(default_factory=dict)
    estimated_cogs: Optional[float] = None
    recorded_expenses: float = 0
    estimated_profit: Optional[float] = None
    profit_note: str = "Estimated profit is unavailable when production cost data is incomplete."


STORAGE_FILE = Path(__file__).with_name("data.json")
_storage_lock = threading.RLock()
DEFAULT_PRODUCTS = (
    ("PROD-001", "Purong Cacao (Tablea) Pouch 100G (11 Pcs)", 120.0, "Pouch", 100.0, 11),
    ("PROD-002", "60% Dark Chocolate with Pistachio Nuts Pouch 20G", 40.0, "Pouch", 20.0, None),
    ("PROD-003", "60% Dark Chocolate with Pistachio Nuts Bar 60G", 150.0, "Bar", 60.0, None),
    ("PROD-004", "60% Dark Chocolate with Mango Bits Pouch 20G", 40.0, "Pouch", 20.0, None),
    ("PROD-005", "60% Dark Chocolate with Mango Bits Bar 60G", 150.0, "Bar", 60.0, None),
)


def load_storage():
    try:
        with STORAGE_FILE.open("r", encoding="utf-8") as storage_file:
            data = json.load(storage_file)
    except FileNotFoundError:
        data = {}

    return {
        "products": {
            key: ProductResponse.model_validate(value)
            for key, value in data.get("products", {}).items()
        },
        "batches": {
            key: ProductionBatchResponse.model_validate(value)
            for key, value in data.get("batches", {}).items()
        },
        "inventory": data.get("inventory", {}),
        "movements": data.get("movements", {}),
        "orders": {
            key: SalesOrderResponse.model_validate(value)
            for key, value in data.get("orders", {}).items()
        },
        "ingredients": data.get("ingredients", {}),
        "expenses": data.get("expenses", {}),
        "events": data.get("events", {}),
    }


def save_storage():
    with _storage_lock:
        data = {
            "products": {key: value.model_dump(mode="json") for key, value in db_products.items()},
            "batches": {key: value.model_dump(mode="json") for key, value in db_batches.items()},
            "inventory": db_inventory,
            "movements": {
                key: value.model_dump(mode="json") if isinstance(value, BaseModel) else value
                for key, value in db_movements.items()
            },
            "orders": {key: value.model_dump(mode="json") for key, value in db_orders.items()},
            "ingredients": db_ingredients,
            "expenses": db_expenses,
            "events": db_events,
        }
        STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=STORAGE_FILE.parent,
                prefix=".data-",
                suffix=".tmp",
                delete=False,
            ) as storage_file:
                temporary_path = Path(storage_file.name)
                json.dump(data, storage_file, ensure_ascii=False, indent=2)
                storage_file.flush()
                os.fsync(storage_file.fileno())
            os.replace(temporary_path, STORAGE_FILE)
        except OSError:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()
            raise


_storage = load_storage()
db_products: Dict[str, ProductResponse] = _storage["products"]
db_batches: Dict[str, ProductionBatchResponse] = _storage["batches"]
db_inventory: Dict[str, float] = _storage["inventory"]
db_movements: Dict[str, dict] = _storage["movements"]
db_orders: Dict[str, SalesOrderResponse] = _storage["orders"]
db_ingredients: Dict[str, dict] = _storage["ingredients"]
db_expenses: Dict[str, dict] = _storage["expenses"]
db_events: Dict[str, dict] = _storage["events"]


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_interview_products()
    yield


app = FastAPI(
    title="Kakina Food Products Mfg. Management API",
    description="API for managing chocolate production, inventory movements, sales orders, and location performance.",
    version="1.0.0",
    lifespan=lifespan,
)


def seed_interview_products() -> None:
    """Add interview products only when neither their ID nor name already exists."""
    existing_names = {product.name.casefold() for product in db_products.values()}
    changed = False
    for product_id, name, price, packaging, weight, pieces in DEFAULT_PRODUCTS:
        if product_id in db_products or name.casefold() in existing_names:
            continue
        db_products[product_id] = ProductResponse(
            product_id=product_id,
            name=name,
            unit_price=price,
            category=packaging,
            packaging=packaging,
            weight_grams=weight,
            pieces_per_pack=pieces,
        )
        existing_names.add(name.casefold())
        changed = True
    if changed:
        save_storage()


@app.get("/", tags=["Health Check"])
def root():
    return {"message": "Kakina Food Products Mfg. Management API is running."}


def _record_movement(
    *,
    product_id: str,
    source: str,
    destination: str,
    quantity: int,
    movement_type: str,
    reason: str = "",
) -> dict:
    movement_id = f"MOV-{datetime.now():%Y%m%d%H%M%S%f}"
    movement = {
        "movement_id": movement_id,
        "timestamp": datetime.now().isoformat(),
        "source_location_id": source,
        "destination_location_id": destination,
        "product_id": product_id,
        "quantity": quantity,
        "movement_type": movement_type,
        "reason": reason,
    }
    db_movements[movement_id] = movement
    return movement


def _reserved_quantity(location_id: str, product_id: str, *, exclude_order_id: str | None = None) -> int:
    reserved = 0
    for order in db_orders.values():
        if order.status != OrderStatus.PENDING or order.order_id == exclude_order_id:
            continue
        if order.location_id != location_id:
            continue
        reserved += sum(
            item.quantity for item in order.items if item.product_id == product_id
        )
    return reserved


def _unit_cost_estimate(product_id: str) -> float | None:
    batches = [batch for batch in db_batches.values() if batch.product_id == product_id]
    quantity = sum(batch.quantity_produced for batch in batches)
    if not quantity:
        return None
    batch_cost = sum(
        batch.total_batch_cost
        + sum(
            expense["amount"]
            for expense in db_expenses.values()
            if expense.get("related_batch_id") == batch.batch_id
        )
        for batch in batches
    )
    return batch_cost / quantity


# --- Product Catalog Endpoints ---

@app.post("/products", response_model=ProductResponse, status_code=Status.HTTP_201_CREATED, tags=["Products"])
def create_product(product: ProductCreate):
    with _storage_lock:
        if product.product_id in db_products:
            raise HTTPException(status_code=409, detail="Product ID already exists.")
        if any(existing.name.casefold() == product.name.casefold() for existing in db_products.values()):
            raise HTTPException(status_code=409, detail="A product with this name already exists.")
        db_products[product.product_id] = ProductResponse(**product.model_dump())
        save_storage()
        return db_products[product.product_id]

@app.get("/products", response_model=List[ProductResponse], tags=["Products"])
def list_products():
    return [product for product in db_products.values() if getattr(product, "active", True)]


@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: str):
    product = db_products.get(product_id)
    if product is None or not getattr(product, "active", True):
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@app.patch("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def update_product(product_id: str, changes: ProductUpdate):
    current = db_products.get(product_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    updated_data = current.model_dump()
    updated_data.update(changes.model_dump(exclude_unset=True))
    updated = ProductResponse.model_validate(updated_data)
    if any(
        other_id != product_id and other.name.casefold() == updated.name.casefold()
        for other_id, other in db_products.items()
    ):
        raise HTTPException(status_code=409, detail="A product with this name already exists.")
    db_products[product_id] = updated
    save_storage()
    return updated


@app.delete("/products/{product_id}", status_code=Status.HTTP_204_NO_CONTENT, tags=["Products"])
def deactivate_product(product_id: str):
    current = db_products.get(product_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    data = current.model_dump()
    data["active"] = False
    db_products[product_id] = ProductResponse.model_validate(data)
    save_storage()


@app.get("/ingredients", tags=["Ingredients"])
def list_ingredients():
    return [
        {
            **item,
            "low_stock": item["current_stock_qty"] <= item.get("reorder_level", 0),
        }
        for item in db_ingredients.values()
        if item.get("active", True)
    ]


@app.post("/ingredients", status_code=Status.HTTP_201_CREATED, tags=["Ingredients"])
def create_ingredient(ingredient: IngredientCreate):
    with _storage_lock:
        if ingredient.ingredient_id in db_ingredients:
            raise HTTPException(status_code=409, detail="Ingredient ID already exists.")
        if any(
            item["name"].casefold() == ingredient.name.casefold()
            for item in db_ingredients.values()
        ):
            raise HTTPException(status_code=409, detail="An ingredient with this name already exists.")
        record = {
            **ingredient.model_dump(),
            "active": True,
            "created_at": datetime.now().isoformat(),
            "movements": [{
                "quantity_change": ingredient.current_stock_qty,
                "reason": "Opening stock",
                "timestamp": datetime.now().isoformat(),
            }] if ingredient.current_stock_qty else [],
        }
        db_ingredients[ingredient.ingredient_id] = record
        save_storage()
        return record


@app.patch("/ingredients/{ingredient_id}", tags=["Ingredients"])
def update_ingredient(ingredient_id: str, changes: IngredientUpdate):
    ingredient = db_ingredients.get(ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found.")
    updates = changes.model_dump(exclude_unset=True)
    if "name" in updates and any(
        key != ingredient_id and item["name"].casefold() == updates["name"].casefold()
        for key, item in db_ingredients.items()
    ):
        raise HTTPException(status_code=409, detail="An ingredient with this name already exists.")
    ingredient.update(updates)
    ingredient["updated_at"] = datetime.now().isoformat()
    save_storage()
    return ingredient


@app.post("/ingredients/{ingredient_id}/adjustments", tags=["Ingredients"])
def adjust_ingredient(ingredient_id: str, adjustment: IngredientAdjustment):
    with _storage_lock:
        ingredient = db_ingredients.get(ingredient_id)
        if ingredient is None or not ingredient.get("active", True):
            raise HTTPException(status_code=404, detail="Active ingredient not found.")
        new_quantity = ingredient["current_stock_qty"] + adjustment.quantity_change
        if adjustment.quantity_change == 0:
            raise HTTPException(status_code=422, detail="Quantity change cannot be zero.")
        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Adjustment would make ingredient stock negative.")
        ingredient["current_stock_qty"] = new_quantity
        ingredient["updated_at"] = datetime.now().isoformat()
        ingredient.setdefault("movements", []).append({
            "quantity_change": adjustment.quantity_change,
            "reason": adjustment.reason,
            "timestamp": datetime.now().isoformat(),
        })
        save_storage()
        return ingredient


# --- Production Management Endpoints ---

@app.post("/batches", response_model=ProductionBatchResponse, status_code=Status.HTTP_201_CREATED, tags=["Production"])
def record_production_batch(batch_in: ProductionBatchCreate):
    with _storage_lock:
        if batch_in.batch_id in db_batches:
            raise HTTPException(status_code=409, detail="Production batch ID already exists.")
        if batch_in.product_id not in db_products:
            raise HTTPException(status_code=404, detail="Product not found.")

        normalized_usage = []
        ingredients_to_deduct: list[tuple[dict, float]] = []
        ingredient_usage_totals: Dict[str, float] = {}
        total_cost = 0.0
        for usage in batch_in.ingredients_used:
            ingredient = None
            if usage.ingredient_id:
                ingredient = db_ingredients.get(usage.ingredient_id)
                if ingredient is None or not ingredient.get("active", True):
                    raise HTTPException(status_code=404, detail=f"Ingredient {usage.ingredient_id} not found.")
            elif usage.ingredient_name:
                ingredient = next(
                    (
                        item for item in db_ingredients.values()
                        if item["name"].casefold() == usage.ingredient_name.casefold()
                        and item.get("active", True)
                    ),
                    None,
                )

            if ingredient is not None:
                used_before = ingredient_usage_totals.get(ingredient["ingredient_id"], 0.0)
                required = used_before + usage.quantity_used
                if ingredient["current_stock_qty"] < required:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient ingredient stock for {ingredient['name']}.",
                    )
                ingredient_usage_totals[ingredient["ingredient_id"]] = required
                cost_per_unit = ingredient["unit_cost"]
                ingredients_to_deduct.append((ingredient, usage.quantity_used))
                ingredient_id = ingredient["ingredient_id"]
                ingredient_name = ingredient["name"]
            else:
                if usage.cost_per_unit is None or not usage.ingredient_name:
                    raise HTTPException(
                        status_code=422,
                        detail="Provide an existing ingredient ID or an ingredient name and cost per unit.",
                    )
                cost_per_unit = usage.cost_per_unit
                ingredient_id = None
                ingredient_name = usage.ingredient_name

            total_cost += usage.quantity_used * cost_per_unit
            normalized_usage.append(IngredientUsage(
                ingredient_id=ingredient_id,
                ingredient_name=ingredient_name,
                quantity_used=usage.quantity_used,
                cost_per_unit=cost_per_unit,
            ))

        batch_response = ProductionBatchResponse(
            batch_id=batch_in.batch_id,
            product_id=batch_in.product_id,
            quantity_produced=batch_in.quantity_produced,
            ingredients_used=normalized_usage,
            production_date=datetime.now(),
            packaging_cost=batch_in.packaging_cost,
            labor_cost=batch_in.labor_cost,
            other_cost=batch_in.other_cost,
            total_batch_cost=(
                total_cost + batch_in.packaging_cost + batch_in.labor_cost + batch_in.other_cost
            ),
            unit_production_cost=(
                total_cost + batch_in.packaging_cost + batch_in.labor_cost + batch_in.other_cost
            ) / batch_in.quantity_produced,
        )
        for ingredient, quantity in ingredients_to_deduct:
            ingredient["current_stock_qty"] -= quantity
            ingredient["updated_at"] = datetime.now().isoformat()
            ingredient.setdefault("movements", []).append({
                "quantity_change": -quantity,
                "reason": f"Consumed by production batch {batch_in.batch_id}",
                "timestamp": datetime.now().isoformat(),
            })

        db_batches[batch_in.batch_id] = batch_response
        central_key = f"LOC-CENTRAL:{batch_in.product_id}"
        db_inventory[central_key] = db_inventory.get(central_key, 0) + batch_in.quantity_produced
        _record_movement(
            product_id=batch_in.product_id,
            source="PRODUCTION",
            destination="LOC-CENTRAL",
            quantity=batch_in.quantity_produced,
            movement_type="production_in",
            reason=f"Production batch {batch_in.batch_id}",
        )
        save_storage()
        return batch_response


@app.get("/batches", response_model=List[ProductionBatchResponse], tags=["Production"])
def list_production_batches(
    product_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    batches = list(db_batches.values())
    if product_id:
        batches = [batch for batch in batches if batch.product_id == product_id]
    if start_date:
        batches = [batch for batch in batches if batch.production_date >= start_date]
    if end_date:
        batches = [batch for batch in batches if batch.production_date <= end_date]
    return sorted(batches, key=lambda batch: batch.production_date, reverse=True)


@app.get("/batches/{batch_id}", response_model=ProductionBatchResponse, tags=["Production"])
def get_production_batch(batch_id: str):
    batch = db_batches.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Production batch not found.")
    return batch


# --- Inventory & Transfer Endpoints ---

@app.post("/inventory/transfer", response_model=InventoryTransferResponse, tags=["Inventory"])
def transfer_stock(movement: InventoryTransferCreate):
    with _storage_lock:
        if movement.movement_id in db_movements:
            raise HTTPException(status_code=409, detail="Movement ID already exists.")
        if movement.source_location_id == movement.destination_location_id:
            raise HTTPException(status_code=422, detail="Source and destination must be different.")
        if movement.product_id not in db_products:
            raise HTTPException(status_code=404, detail="Product not found.")
        src_key = f"{movement.source_location_id}:{movement.product_id}"
        dst_key = f"{movement.destination_location_id}:{movement.product_id}"

        current_src_stock = db_inventory.get(src_key, 0)
        reserved = _reserved_quantity(movement.source_location_id, movement.product_id)
        if current_src_stock - reserved < movement.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient unreserved inventory at {movement.source_location_id}. "
                f"Available: {current_src_stock - reserved}",
            )

        db_inventory[src_key] = current_src_stock - movement.quantity
        db_inventory[dst_key] = db_inventory.get(dst_key, 0) + movement.quantity
        record = InventoryTransferResponse(
            **movement.model_dump(),
            timestamp=datetime.now(),
            movement_type="transfer",
            reason="Location transfer",
        )
        db_movements[movement.movement_id] = record.model_dump(mode="json")
        save_storage()
        return record

@app.get("/inventory/stock", tags=["Inventory"])
def get_stock_levels(location_id: Optional[str] = Query(None)):
    """Retrieve current stock quantities across locations."""
    results = []
    for key, qty in db_inventory.items():
        loc, prod_id = key.split(":")
        if location_id and loc != location_id:
            continue
        reserved = _reserved_quantity(loc, prod_id)
        results.append({
            "location_id": loc,
            "product_id": prod_id,
            "product_name": db_products[prod_id].name if prod_id in db_products else "Unknown",
            "quantity_on_hand": qty,
            "quantity_reserved": reserved,
            "quantity_available": qty - reserved,
        })
    return results


@app.get("/inventory/movements", tags=["Inventory"])
def list_inventory_movements(
    location_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
):
    results = list(db_movements.values())
    if location_id:
        results = [
            item for item in results
            if item.get("source_location_id") == location_id
            or item.get("destination_location_id") == location_id
        ]
    if product_id:
        results = [item for item in results if item.get("product_id") == product_id]
    return sorted(results, key=lambda item: item.get("timestamp", ""), reverse=True)


@app.post("/inventory/adjustments", tags=["Inventory"])
def adjust_inventory(adjustment: InventoryAdjustment):
    with _storage_lock:
        if adjustment.product_id not in db_products:
            raise HTTPException(status_code=404, detail="Product not found.")
        if adjustment.quantity_change == 0:
            raise HTTPException(status_code=422, detail="Quantity change cannot be zero.")
        key = f"{adjustment.location_id}:{adjustment.product_id}"
        current = db_inventory.get(key, 0)
        updated = current + adjustment.quantity_change
        reserved = _reserved_quantity(adjustment.location_id, adjustment.product_id)
        if updated < reserved:
            raise HTTPException(
                status_code=400,
                detail=f"Adjustment would reduce stock below the {reserved} unit(s) reserved.",
            )
        db_inventory[key] = updated
        movement = _record_movement(
            product_id=adjustment.product_id,
            source=adjustment.location_id if adjustment.quantity_change < 0 else "COUNT_ADJUSTMENT",
            destination="COUNT_ADJUSTMENT" if adjustment.quantity_change < 0 else adjustment.location_id,
            quantity=adjustment.quantity_change,
            movement_type="count_adjustment",
            reason=adjustment.reason,
        )
        save_storage()
        return {"stock": updated, "movement": movement}


@app.get("/events", tags=["Events"])
def list_events(status_filter: Optional[str] = Query(None)):
    events = list(db_events.values())
    if status_filter:
        events = [event for event in events if event["status"] == status_filter.casefold()]
    return sorted(events, key=lambda event: event.get("event_date") or "", reverse=True)


@app.post("/events", status_code=Status.HTTP_201_CREATED, tags=["Events"])
def create_event(event: EventCreate):
    with _storage_lock:
        if event.event_id in db_events:
            raise HTTPException(status_code=409, detail="Event ID already exists.")
        record = {
            **event.model_dump(mode="json"),
            "location_id": event.event_id,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "closed_at": None,
            "unsold_returned": {},
        }
        db_events[event.event_id] = record
        save_storage()
        return record


@app.get("/events/{event_id}", tags=["Events"])
def get_event(event_id: str):
    event = db_events.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


@app.post("/events/{event_id}/close", tags=["Events"])
def close_event(event_id: str):
    with _storage_lock:
        event = db_events.get(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found.")
        if event["status"] != "open":
            raise HTTPException(status_code=409, detail="Event is already closed.")
        location_id = event["location_id"]
        event_inventory = {
            key: quantity for key, quantity in db_inventory.items()
            if key.startswith(f"{location_id}:") and quantity > 0
        }
        reserved_lines = [
            order.order_id
            for order in db_orders.values()
            if order.status == OrderStatus.PENDING and order.location_id == location_id
        ]
        if reserved_lines:
            raise HTTPException(
                status_code=409,
                detail="Cancel or complete pending reservations for this event before closing it.",
            )
        returned: dict[str, int] = {}
        for key, quantity in event_inventory.items():
            quantity = int(quantity)
            product_id = key.split(":", 1)[1]
            central_key = f"LOC-CENTRAL:{product_id}"
            db_inventory[key] = 0
            db_inventory[central_key] = db_inventory.get(central_key, 0) + quantity
            returned[product_id] = quantity
            _record_movement(
                product_id=product_id,
                source=location_id,
                destination="LOC-CENTRAL",
                quantity=quantity,
                movement_type="event_return",
                reason=f"Unsold stock returned when closing event {event_id}",
            )
        event["status"] = "closed"
        event["closed_at"] = datetime.now().isoformat()
        event["unsold_returned"] = returned
        save_storage()
        return event


@app.get("/expenses", tags=["Expenses"])
def list_expenses(
    category: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    expenses = list(db_expenses.values())
    if category:
        expenses = [item for item in expenses if item["category"].casefold() == category.casefold()]
    if location_id:
        expenses = [item for item in expenses if item.get("location_id") == location_id]
    if start_date:
        expenses = [
            item for item in expenses
            if date.fromisoformat(item["expense_date"][:10]) >= start_date
        ]
    if end_date:
        expenses = [
            item for item in expenses
            if date.fromisoformat(item["expense_date"][:10]) <= end_date
        ]
    return sorted(expenses, key=lambda item: item["expense_date"], reverse=True)


@app.post("/expenses", status_code=Status.HTTP_201_CREATED, tags=["Expenses"])
def create_expense(expense: ExpenseCreate):
    with _storage_lock:
        if expense.expense_id in db_expenses:
            raise HTTPException(status_code=409, detail="Expense ID already exists.")
        if expense.related_batch_id and expense.related_batch_id not in db_batches:
            raise HTTPException(status_code=404, detail="Related production batch not found.")
        record = expense.model_dump(mode="json")
        record["expense_date"] = (
            expense.expense_date or datetime.now()
        ).isoformat()
        record["created_at"] = datetime.now().isoformat()
        db_expenses[expense.expense_id] = record
        save_storage()
        return record


@app.put("/expenses/{expense_id}", tags=["Expenses"])
def update_expense(expense_id: str, changes: ExpenseUpdate):
    with _storage_lock:
        expense = db_expenses.get(expense_id)
        if expense is None:
            raise HTTPException(status_code=404, detail="Expense not found.")
        updates = changes.model_dump(exclude_unset=True, mode="json")
        if updates.get("related_batch_id") and updates["related_batch_id"] not in db_batches:
            raise HTTPException(status_code=404, detail="Related production batch not found.")
        expense.update(updates)
        expense["updated_at"] = datetime.now().isoformat()
        save_storage()
        return expense


@app.delete("/expenses/{expense_id}", status_code=Status.HTTP_204_NO_CONTENT, tags=["Expenses"])
def delete_expense(expense_id: str):
    if expense_id not in db_expenses:
        raise HTTPException(status_code=404, detail="Expense not found.")
    del db_expenses[expense_id]
    save_storage()


# --- Sales & Reservation Endpoints ---

@app.post("/orders", response_model=SalesOrderResponse, status_code=Status.HTTP_201_CREATED, tags=["Sales & Orders"])
def create_sales_order(order_in: SalesOrderCreate):
    with _storage_lock:
        if order_in.order_id in db_orders:
            raise HTTPException(status_code=409, detail="Order ID already exists.")

        quantity_by_product: Dict[str, int] = {}
        for item in order_in.items:
            quantity_by_product[item.product_id] = quantity_by_product.get(item.product_id, 0) + item.quantity

        processed_items: List[OrderItemResponse] = []
        total_items_cost = 0.0
        estimated_cogs = 0.0
        cogs_is_known = True
        for product_id, quantity in quantity_by_product.items():
            product = db_products.get(product_id)
            if product is None or not getattr(product, "active", True):
                raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found.")
            stock_key = f"{order_in.location_id}:{product_id}"
            available_stock = db_inventory.get(stock_key, 0) - _reserved_quantity(
                order_in.location_id, product_id
            )
            if available_stock < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient unreserved stock at {order_in.location_id} "
                    f"for {product.name}. Available: {available_stock}",
                )
            subtotal = quantity * product.unit_price
            total_items_cost += subtotal
            processed_items.append(OrderItemResponse(
                product_id=product_id,
                quantity=quantity,
                unit_price=product.unit_price,
                subtotal=subtotal,
            ))
            unit_cost = _unit_cost_estimate(product_id)
            if unit_cost is None:
                cogs_is_known = False
            else:
                estimated_cogs += unit_cost * quantity

        if order_in.status == OrderStatus.CANCELLED:
            raise HTTPException(status_code=422, detail="Create as pending or completed, not cancelled.")

        if order_in.status == OrderStatus.COMPLETED:
            for item in processed_items:
                key = f"{order_in.location_id}:{item.product_id}"
                db_inventory[key] -= item.quantity
        if not cogs_is_known or order_in.status == OrderStatus.PENDING:
            estimated_cogs_value = None
        else:
            estimated_cogs_value = estimated_cogs

        order_record = SalesOrderResponse(
            order_id=order_in.order_id,
            timestamp=datetime.now(),
            channel=order_in.channel,
            location_id=order_in.location_id,
            customer_name=order_in.customer_name,
            messenger_account=order_in.messenger_account,
            contact_number=order_in.contact_number,
            items=processed_items,
            total_amount=total_items_cost + order_in.delivery_fee,
            payment_method=order_in.payment_method,
            fulfillment=order_in.fulfillment,
            delivery_fee=order_in.delivery_fee,
            status=order_in.status,
            estimated_cogs=estimated_cogs_value,
        )
        db_orders[order_in.order_id] = order_record
        for item in processed_items:
            if order_in.status == OrderStatus.COMPLETED:
                _record_movement(
                    product_id=item.product_id,
                    source=order_in.location_id,
                    destination="CUSTOMER",
                    quantity=-item.quantity,
                    movement_type="sale",
                    reason=f"Completed order {order_in.order_id}",
                )
            else:
                _record_movement(
                    product_id=item.product_id,
                    source=order_in.location_id,
                    destination=f"RESERVATION:{order_in.order_id}",
                    quantity=item.quantity,
                    movement_type="reservation_hold",
                    reason=f"Stock held for pending reservation {order_in.order_id}",
                )
        save_storage()
        return order_record


@app.get("/orders", response_model=List[SalesOrderResponse], tags=["Sales & Orders"])
def list_sales_orders(
    status_filter: Optional[OrderStatus] = Query(None),
    location_id: Optional[str] = Query(None),
):
    orders = list(db_orders.values())
    if status_filter:
        orders = [order for order in orders if order.status == status_filter]
    if location_id:
        orders = [order for order in orders if order.location_id == location_id]
    return sorted(orders, key=lambda order: order.timestamp, reverse=True)


@app.get("/orders/{order_id}", response_model=SalesOrderResponse, tags=["Sales & Orders"])
def get_sales_order(order_id: str):
    order = db_orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@app.post("/orders/{order_id}/complete", response_model=SalesOrderResponse, tags=["Sales & Orders"])
def complete_reservation(order_id: str):
    with _storage_lock:
        order = db_orders.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found.")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=409, detail="Only pending reservations can be completed.")
        cogs = 0.0
        cogs_is_known = True
        for item in order.items:
            key = f"{order.location_id}:{item.product_id}"
            if (
                db_inventory.get(key, 0)
                - _reserved_quantity(order.location_id, item.product_id, exclude_order_id=order_id)
                < item.quantity
            ):
                raise HTTPException(
                    status_code=409,
                    detail=f"Reserved stock is no longer available for {item.product_id}.",
                )
            unit_cost = _unit_cost_estimate(item.product_id)
            if unit_cost is None:
                cogs_is_known = False
            else:
                cogs += unit_cost * item.quantity
        for item in order.items:
            key = f"{order.location_id}:{item.product_id}"
            db_inventory[key] -= item.quantity
            _record_movement(
                product_id=item.product_id,
                source=order.location_id,
                destination="CUSTOMER",
                quantity=-item.quantity,
                movement_type="sale",
                reason=f"Reservation {order_id} completed",
            )
        order.status = OrderStatus.COMPLETED
        order.estimated_cogs = cogs if cogs_is_known else None
        save_storage()
        return order


@app.post("/orders/{order_id}/cancel", response_model=SalesOrderResponse, tags=["Sales & Orders"])
def cancel_reservation(order_id: str):
    with _storage_lock:
        order = db_orders.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found.")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=409, detail="Only pending reservations can be cancelled.")
        order.status = OrderStatus.CANCELLED
        for item in order.items:
            _record_movement(
                product_id=item.product_id,
                source=f"RESERVATION:{order_id}",
                destination=order.location_id,
                quantity=item.quantity,
                movement_type="reservation_release",
                reason=f"Pending reservation {order_id} cancelled",
            )
        save_storage()
        return order


# --- Reports & Analytics Endpoints ---

@app.get("/reports/sales-summary", response_model=SalesSummaryResponse, tags=["Analytics"])
def get_sales_summary(
    location_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    orders = _completed_orders(location_id, start_date, end_date)
    return _sales_summary(orders, start_date, end_date, location_id)


def _completed_orders(
    location_id: str | None,
    start_date: date | None,
    end_date: date | None,
) -> list[SalesOrderResponse]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date.")
    orders = [order for order in db_orders.values() if order.status == OrderStatus.COMPLETED]
    if location_id:
        orders = [order for order in orders if order.location_id == location_id]
    if start_date:
        orders = [order for order in orders if order.timestamp.date() >= start_date]
    if end_date:
        orders = [order for order in orders if order.timestamp.date() <= end_date]
    return orders


def _expense_totals(
    start_date: date | None,
    end_date: date | None,
    location_id: str | None = None,
) -> tuple[float, float]:
    expenses = list(db_expenses.values())
    if start_date:
        expenses = [
            item for item in expenses
            if date.fromisoformat(item["expense_date"][:10]) >= start_date
        ]
    if end_date:
        expenses = [
            item for item in expenses
            if date.fromisoformat(item["expense_date"][:10]) <= end_date
        ]
    if location_id:
        expenses = [item for item in expenses if item.get("location_id") in {None, location_id}]
    total = sum(item["amount"] for item in expenses)
    production_categories = {"raw materials", "packaging", "labor"}
    operating = sum(
        item["amount"] for item in expenses
        if item["category"].casefold() not in production_categories
        and not item.get("related_batch_id")
    )
    return total, operating


def _sales_summary(
    orders: list[SalesOrderResponse],
    start_date: date | None = None,
    end_date: date | None = None,
    location_id: str | None = None,
) -> SalesSummaryResponse:
    gross_revenue = sum(order.total_amount for order in orders)
    total_items_sold = sum(
        item.quantity for order in orders for item in order.items
    )
    channel_breakdown: Dict[str, float] = {channel.value: 0.0 for channel in OrderChannel}
    for order in orders:
        channel_breakdown[order.channel.value] += order.total_amount

    estimated_cogs = 0.0
    cogs_is_known = True
    for order in orders:
        for item in order.items:
            unit_cost = _unit_cost_estimate(item.product_id)
            if unit_cost is None:
                cogs_is_known = False
            else:
                estimated_cogs += unit_cost * item.quantity
    total_expenses, operating_expenses = _expense_totals(start_date, end_date, location_id)
    estimated_cogs_value = estimated_cogs if cogs_is_known else None
    estimated_profit = (
        gross_revenue - estimated_cogs - operating_expenses
        if cogs_is_known else None
    )
    return SalesSummaryResponse(
        total_orders=len(orders),
        gross_revenue=gross_revenue,
        total_items_sold=total_items_sold,
        revenue_by_channel=channel_breakdown,
        estimated_cogs=estimated_cogs_value,
        recorded_expenses=total_expenses,
        estimated_profit=estimated_profit,
        profit_note=(
            "Estimated profit = completed sales revenue − estimated production cost "
            "of sold items − operating expenses. Raw-material purchases not tied to "
            "production are reported as expenses but excluded from this estimate."
            if cogs_is_known
            else "Estimated profit is unavailable because at least one sold product has no production cost history."
        ),
    )


@app.get("/reports/daily-sales", tags=["Analytics"])
def daily_sales(report_date: date = Query(default_factory=date.today)):
    orders = _completed_orders(None, report_date, report_date)
    return {
        "report_date": report_date.isoformat(),
        **_sales_summary(orders, report_date, report_date).model_dump(),
    }


@app.get("/reports/dashboard", tags=["Analytics"])
def dashboard():
    active_products = [item for item in db_products.values() if getattr(item, "active", True)]
    active_ingredients = [
        item for item in db_ingredients.values() if item.get("active", True)
    ]
    stock_rows = get_stock_levels(location_id=None)
    available_by_product: Dict[str, int] = {}
    for row in stock_rows:
        available_by_product[row["product_id"]] = (
            available_by_product.get(row["product_id"], 0) + row["quantity_available"]
        )
    low_stock_products = [
        {
            "product_id": product.product_id,
            "product_name": product.name,
            "available_quantity": available_by_product.get(product.product_id, 0),
            "reorder_level": product.reorder_level,
        }
        for product in active_products
        if available_by_product.get(product.product_id, 0) <= product.reorder_level
    ]
    pending_orders = [
        order for order in db_orders.values() if order.status == OrderStatus.PENDING
    ]
    sales_today = _sales_summary(
        _completed_orders(None, date.today(), date.today()),
        date.today(),
        date.today(),
    )
    all_sales = _sales_summary(_completed_orders(None, None, None))
    return {
        "total_products": len(active_products),
        "total_ingredients": len(active_ingredients),
        "low_stock_ingredients": [
            {"ingredient_id": item["ingredient_id"], "name": item["name"]}
            for item in active_ingredients
            if item["current_stock_qty"] <= item.get("reorder_level", 0)
        ],
        "available_finished_stock": sum(available_by_product.values()),
        "low_stock_products": low_stock_products,
        "production_batches": len(db_batches),
        "pending_reservations": len(pending_orders),
        "open_events": sum(event["status"] == "open" for event in db_events.values()),
        "total_sales": all_sales.gross_revenue,
        "sales_summary": all_sales.model_dump(),
        "sales_today": sales_today.model_dump(),
    }


@app.get("/reports/low-stock", tags=["Analytics"])
def low_stock_report():
    current = dashboard()
    return {
        "products": current["low_stock_products"],
        "ingredients": current["low_stock_ingredients"],
    }


@app.get("/reports/product-sales", tags=["Analytics"])
def product_sales(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    location_id: Optional[str] = Query(None),
):
    orders = _completed_orders(location_id, start_date, end_date)
    totals: Dict[str, dict] = {}
    for order in orders:
        for item in order.items:
            product = db_products.get(item.product_id)
            row = totals.setdefault(item.product_id, {
                "product_id": item.product_id,
                "product_name": product.name if product else "Unknown",
                "quantity_sold": 0,
                "revenue": 0.0,
            })
            row["quantity_sold"] += item.quantity
            row["revenue"] += item.subtotal
    return sorted(totals.values(), key=lambda row: (-row["quantity_sold"], row["product_name"]))


@app.get("/reports/best-sellers", tags=["Analytics"])
def best_sellers(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    location_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
):
    return product_sales(start_date, end_date, location_id)[:limit]


@app.get("/reports/location-sales", tags=["Analytics"])
def location_sales(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    orders = _completed_orders(None, start_date, end_date)
    locations: Dict[str, dict] = {}
    for order in orders:
        row = locations.setdefault(order.location_id, {
            "location_id": order.location_id,
            "location_name": next(
                (
                    event.get("location_name") or event.get("name")
                    for event in db_events.values()
                    if event["location_id"] == order.location_id
                ),
                order.location_id,
            ),
            "total_orders": 0,
            "items_sold": 0,
            "gross_revenue": 0.0,
        })
        row["total_orders"] += 1
        row["items_sold"] += sum(item.quantity for item in order.items)
        row["gross_revenue"] += order.total_amount
    return sorted(locations.values(), key=lambda row: row["location_id"])


@app.get("/reports/production-costs", tags=["Analytics"])
def production_costs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    batches = list(db_batches.values())
    if start_date:
        batches = [batch for batch in batches if batch.production_date >= start_date]
    if end_date:
        batches = [batch for batch in batches if batch.production_date <= end_date]
    return {
        "batch_count": len(batches),
        "units_produced": sum(batch.quantity_produced for batch in batches),
        "total_production_cost": sum(
            batch.total_batch_cost
            + sum(
                expense["amount"]
                for expense in db_expenses.values()
                if expense.get("related_batch_id") == batch.batch_id
            )
            for batch in batches
        ),
        "batches": [batch.model_dump(mode="json") for batch in batches],
    }


@app.get("/reports/expenses", tags=["Analytics"])
def expense_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    expenses = list_expenses(
        category=None,
        location_id=None,
        start_date=start_date,
        end_date=end_date,
    )
    by_category: Dict[str, float] = {}
    for expense in expenses:
        by_category[expense["category"]] = (
            by_category.get(expense["category"], 0.0) + expense["amount"]
        )
    return {
        "expense_count": len(expenses),
        "total_expenses": sum(item["amount"] for item in expenses),
        "by_category": by_category,
        "expenses": expenses,
    }


@app.get("/reports/financial-summary", tags=["Analytics"])
def financial_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    orders = _completed_orders(None, start_date, end_date)
    return _sales_summary(orders, start_date, end_date).model_dump()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)