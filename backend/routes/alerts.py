"""
alerts.py - Alert API Routes

Endpoints:
    GET /alerts              - List all alerts
    GET /alerts/{product_id} - List alerts for a specific product
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.schemas import AlertResponse
from backend.services.alert_service import get_all_alerts, get_alerts_by_product
from backend.db.models import Alert
from backend.services.auth import require_role

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    """
    Retrieve all alerts across all products, most recent first.

    Returns:
        List of alert records with product names
    """
    return get_all_alerts(db)


@router.get("/{product_id}")
def list_product_alerts(
    product_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
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
            "store_id": a.store_id,
            "message": a.message,
            "status": a.status,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.post("/{alert_id}/status")
def update_alert_status(
    alert_id: int,
    status: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager"})),
):
    """Update alert lifecycle status: open/ack/resolved."""
    status = status.lower()
    if status not in {"open", "ack", "resolved"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = status
    db.commit()
    db.refresh(alert)
    return {"id": alert.id, "status": alert.status}
