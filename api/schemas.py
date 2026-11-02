from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, PositiveInt


# ==========================================
# Enums for System Status & Categories
# ==========================================

class PackagingType(str, Enum):
    POUCH = "Pouch"
    BAR = "Bar"


class UnitType(str, Enum):
    GRAMS = "g"
    KILOGRAMS = "kg"
    PIECES = "pcs"
    PACKS = "packs"


class OrderChannel(str, Enum):
    BOOTH = "Booth Sale"
    MESSENGER = "Messenger Order"
    DIRECT_OFFERING = "Direct Sale (Pag-aalok)"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    GCASH = "GCash"


class FulfillmentType(str, Enum):
    PICKUP = "Store Pickup"
    DELIVERY = "Delivery"


class OrderStatus(str, Enum):
    RESERVED = "Reserved"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class MovementType(str, Enum):
    PRODUCTION_IN = "Production Stock In"
    BOOTH_TRANSFER_OUT = "Transfer to Booth"
    BOOTH_RETURN_IN = "Return from Booth"
    DIRECT_SALE_OUT = "Direct Sale Stock Out"
    SPOILAGE_ADJUSTMENT = "Spoilage / Loss"


# ==========================================
# Core Domain Schemas
# ==========================================

class Ingredient(BaseModel):
    """Raw materials harvested or purchased for production."""
    ingredient_id: str = Field(..., json_schema_extra={"example": "ING-001"})
    name: str = Field(..., json_schema_extra={"example": "Cacao Beans"})
    unit: UnitType = Field(..., json_schema_extra={"example": UnitType.KILOGRAMS.value})
    cost_per_unit: float = Field(..., ge=0.0, description="Cost in PHP")
    current_stock_qty: float = Field(..., ge=0.0)


class IngredientUsage(BaseModel):
    """Tracks raw materials consumed per production batch."""
    ingredient_id: str
    quantity_used: float = Field(..., gt=0.0)
    subtotal_cost: float = Field(..., ge=0.0, description="Computed cost in PHP")


class Product(BaseModel):
    """Chocolate product catalog master data."""
    product_id: str = Field(..., json_schema_extra={"example": "PROD-001"})
    name: str = Field(..., json_schema_extra={"example": "60% Dark Chocolate with Pistachio Nuts"})
    packaging: PackagingType = Field(..., json_schema_extra={"example": PackagingType.BAR.value})
    weight_grams: float = Field(..., gt=0.0, json_schema_extra={"example": 60.0})
    unit_price: float = Field(..., ge=0.0, json_schema_extra={"example": 150.0}, description="Price in PHP")
    pieces_per_pack: Optional[int] = Field(None, json_schema_extra={"example": 11}, description="E.g., 11 pcs for Tablea")
    reorder_level: int = Field(default=10, ge=0, description="Threshold for low-stock warning")


class ProductionBatch(BaseModel):
    """Chocolate production run and expense computation."""
    batch_id: str = Field(..., json_schema_extra={"example": "BATCH-20261102-01"})
    production_date: datetime = Field(default_factory=datetime.now)
    product_id: str
    quantity_produced: PositiveInt = Field(..., json_schema_extra={"example": 50})
    ingredients_used: List[IngredientUsage]
    total_batch_cost: float = Field(..., ge=0.0, description="Sum of ingredient costs")
    unit_production_cost: float = Field(..., ge=0.0, description="Cost per unit produced")
    notes: Optional[str] = None


class Location(BaseModel):
    """Sales and stock points (Central Storage or Booth Events)."""
    location_id: str = Field(..., json_schema_extra={"example": "LOC-CLSU"})
    name: str = Field(..., json_schema_extra={"example": "CLSU Booth Event"})
    province: str = Field(default="Nueva Ecija")
    is_event_booth: bool = Field(default=True)


class InventoryMovement(BaseModel):
    """Audit trail for stock transfers, booth disbursements, and returns."""
    movement_id: str = Field(..., json_schema_extra={"example": "MOV-1002"})
    timestamp: datetime = Field(default_factory=datetime.now)
    product_id: str
    source_location_id: str = Field(..., json_schema_extra={"example": "LOC-CENTRAL"})
    destination_location_id: str = Field(..., json_schema_extra={"example": "LOC-TALAVERA"})
    quantity: PositiveInt
    movement_type: MovementType


class OrderItem(BaseModel):
    """Individual item line within a sales transaction or reservation."""
    product_id: str
    quantity: PositiveInt
    unit_price: float = Field(..., ge=0.0)
    subtotal: float = Field(..., ge=0.0)


class SalesOrder(BaseModel):
    """Complete sales transaction, reservation, or booth checkout."""
    order_id: str = Field(..., json_schema_extra={"example": "ORD-20261102-088"})
    timestamp: datetime = Field(default_factory=datetime.now)
    channel: OrderChannel
    location_id: str = Field(..., description="Where the transaction took place")
    
    # Customer Details (Optional for quick cash booth sales, required for reservations)
    customer_name: Optional[str] = Field(None, json_schema_extra={"example": "Juan Dela Cruz"})
    messenger_account: Optional[str] = Field(None, json_schema_extra={"example": "fb.com/juandelacruz"})
    contact_number: Optional[str] = None
    
    # Order Content & Payment
    items: List[OrderItem]
    total_amount: float = Field(..., ge=0.0)
    payment_method: PaymentMethod
    
    # Fulfillment
    fulfillment: FulfillmentType
    delivery_fee: float = Field(default=0.0, ge=0.0)
    status: OrderStatus = Field(default=OrderStatus.COMPLETED)


# ==========================================
# Reporting / Aggregations Schemas
# ==========================================

class DailyLocationReport(BaseModel):
    """Aggregated sales report by location/booth for daily summaries."""
    report_date: datetime
    location_id: str
    total_items_sold: int
    gross_revenue: float
    total_orders: int
    unsold_retained_stock: int