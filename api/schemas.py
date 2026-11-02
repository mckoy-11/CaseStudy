"""Canonical request and response models for the Kakina API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, PositiveInt


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
