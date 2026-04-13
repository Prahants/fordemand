"""
schemas.py - Pydantic Models for API Request/Response Validation

Defines input and output schemas that FastAPI uses for:
- Request body validation
- Response serialization
- OpenAPI documentation generation
"""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


# ─── Product Schemas ──────────────────────────────────────────────

class ProductCreate(BaseModel):
    """Schema for creating a new product."""
    name: str
    category: str
    sku: Optional[str] = None
    supplier_id: Optional[int] = None


class ProductResponse(BaseModel):
    """Schema for product API responses."""
    id: int
    name: str
    category: str
    sku: Optional[str] = None
    supplier_id: Optional[int] = None

    model_config = {"from_attributes": True}


# ─── Inventory Schemas ────────────────────────────────────────────

class InventoryUpdate(BaseModel):
    """Schema for updating inventory stock level."""
    product_id: int
    store_id: int = 1
    stock: int
    reorder_threshold: Optional[int] = None


class InventoryResponse(BaseModel):
    """Schema for inventory API responses."""
    id: int
    product_id: int
    store_id: int
    stock: int
    reorder_threshold: int
    last_updated: Optional[datetime] = None
    product_name: Optional[str] = None
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Sales Schemas ────────────────────────────────────────────────

class SalesCreate(BaseModel):
    """Schema for adding a new sales record."""
    product_id: int
    store_id: int = 1
    date: date
    quantity_sold: int
    promotion_flag: bool = False
    season_tag: Optional[str] = None


class SalesResponse(BaseModel):
    """Schema for sales API responses."""
    id: int
    product_id: int
    store_id: int
    date: date
    quantity_sold: int
    promotion_flag: bool = False
    season_tag: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Forecast Schemas ─────────────────────────────────────────────

class ForecastResponse(BaseModel):
    """Schema for a single forecast prediction."""
    id: int
    product_id: int
    predicted_value: float
    date: date

    model_config = {"from_attributes": True}


class ForecastResult(BaseModel):
    """
    Full forecast result returned by the API, including
    predictions, business metrics, and model evaluation.
    """
    product_id: int
    forecasts: List[ForecastResponse]
    safety_stock: Optional[float] = None
    reorder_point: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    method: str = "prophet"  # "prophet" or "moving_average"


# ─── Alert Schemas ────────────────────────────────────────────────

class AlertResponse(BaseModel):
    """Schema for alert API responses."""
    id: int
    product_id: int
    store_id: int
    message: str
    status: str = "open"
    created_at: Optional[datetime] = None
    product_name: Optional[str] = None
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SupplierCreate(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


class StoreCreate(BaseModel):
    name: str
    location: Optional[str] = None
    store_type: str = "store"


class StoreResponse(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    store_type: str

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


class ForecastLogResponse(BaseModel):
    id: int
    product_id: int
    store_id: int
    horizon_date: date
    predicted_demand: float
    actual_demand: Optional[float] = None
    variance: Optional[float] = None
    generated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class QRCodeCreate(BaseModel):
    product: str
    sku: str
    category: str
    price: float
    qr_payload: str


class QRCodeResponse(BaseModel):
    id: int
    product: str
    sku: str
    category: str
    price: float
    qr_payload: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
