"""
alerts.py - Alert API Routes

Endpoints:
    GET /alerts              - List all alerts
    GET /alerts/{product_id} - List alerts for a specific product
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.schemas import AlertResponse
from backend.services.alert_service import get_all_alerts, get_alerts_by_product

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db)):
    """
    Retrieve all alerts across all products, most recent first.

    Returns:
        List of alert records with product names
    """
    return get_all_alerts(db)


@router.get("/{product_id}")
def list_product_alerts(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve alerts for a specific product.

    Args:
        product_id: ID of the product

    Returns:
        List of alerts for the given product
    """
    alerts = get_alerts_by_product(db, product_id)
    return [
        {
            "id": a.id,
            "product_id": a.product_id,
            "message": a.message,
            "created_at": a.created_at,
        }
        for a in alerts
    ]
