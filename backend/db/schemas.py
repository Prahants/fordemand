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


class ProductResponse(BaseModel):
    """Schema for product API responses."""
    id: int
    name: str
    category: str

    model_config = {"from_attributes": True}


# ─── Inventory Schemas ────────────────────────────────────────────

class InventoryUpdate(BaseModel):
    """Schema for updating inventory stock level."""
    product_id: int
    stock: int
    reorder_threshold: Optional[int] = None


class InventoryResponse(BaseModel):
    """Schema for inventory API responses."""
    id: int
    product_id: int
    stock: int
    reorder_threshold: int
    last_updated: Optional[datetime] = None
    product_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Sales Schemas ────────────────────────────────────────────────

class SalesCreate(BaseModel):
    """Schema for adding a new sales record."""
    product_id: int
    date: date
    quantity_sold: int


class SalesResponse(BaseModel):
    """Schema for sales API responses."""
    id: int
    product_id: int
    date: date
    quantity_sold: int

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
    message: str
    created_at: Optional[datetime] = None
    product_name: Optional[str] = None

    model_config = {"from_attributes": True}
