"""
forecast.py - Forecast API Routes

Endpoints:
    GET /forecast/{product_id} - Run demand forecast for a product

This endpoint triggers the full forecasting pipeline:
    1. Fetch sales data
    2. Run Prophet model
    3. Calculate safety stock & reorder point
    4. Store forecasts in DB
    5. Generate alerts if needed
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Product
from backend.services.forecasting import run_forecast_pipeline
from backend.services.inventory_service import DEFAULT_LEAD_TIME, DEFAULT_Z_SCORE
from backend.services.auth import require_role

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("/{product_id}")
def get_forecast(
    product_id: int,
    store_id: int = Query(default=1, description="Store ID"),
    lead_time: int = Query(default=DEFAULT_LEAD_TIME, description="Lead time in days"),
    service_level: float = Query(default=DEFAULT_Z_SCORE, description="Z-score for service level"),
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    """
    Run the full demand forecasting pipeline for a product.

    Configurable parameters:
        - lead_time: Replenishment lead time in days (default: 3)
        - service_level: Z-score for safety stock calculation (default: 1.65)

    Returns:
        Forecast results including predictions, safety stock,
        reorder point, model evaluation metrics, and any alerts.

    Raises:
        404: If product doesn't exist
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    # Run the forecast pipeline
    try:
        result = run_forecast_pipeline(
            db=db,
            product_id=product_id,
            store_id=store_id,
            lead_time=lead_time,
            z_score=service_level,
        )
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=(
                "Forecasting could not be completed. The sales data may be "
                "insufficient or contain anomalies. Please add more sales "
                "history and try again."
            ),
        )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
