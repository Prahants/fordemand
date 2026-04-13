"""
alert_service.py - Alert Generation Service

Checks inventory levels against calculated reorder points
and generates alerts when stock falls below the threshold.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.db.models import Alert, Inventory, Product


def check_and_create_alerts(
    db: Session,
    product_id: int,
    current_stock: int,
    reorder_point: float,
) -> Alert | None:
    """
    Check if current stock is below the reorder point and create an alert.

    Alert Logic: If stock < reorder_point → create alert

    Args:
        db: Database session
        product_id: Product ID to check
        current_stock: Current stock level
        reorder_point: Calculated reorder point

    Returns:
        Alert object if created, None otherwise
    """
    if current_stock < reorder_point:
        # Get product name for a descriptive alert message
        product = db.query(Product).filter(Product.id == product_id).first()
        product_name = product.name if product else f"Product #{product_id}"

        message = (
            f"⚠️ LOW STOCK ALERT: '{product_name}' has {current_stock} units. "
            f"Reorder point is {reorder_point:.0f} units. Restock immediately!"
        )

        alert = Alert(
            product_id=product_id,
            message=message,
            created_at=datetime.now(timezone.utc),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    return None


def get_all_alerts(db: Session) -> list:
    """
    Retrieve all alerts with product names, ordered by most recent.

    Returns:
        List of dicts with alert data and product names
    """
    results = (
        db.query(Alert, Product.name)
        .join(Product, Alert.product_id == Product.id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    alerts_list = []
    for alert, product_name in results:
        alerts_list.append({
            "id": alert.id,
            "product_id": alert.product_id,
            "message": alert.message,
            "created_at": alert.created_at,
            "product_name": product_name,
        })
    return alerts_list


def get_alerts_by_product(db: Session, product_id: int) -> list:
    """Retrieve alerts for a specific product."""
    return (
        db.query(Alert)
        .filter(Alert.product_id == product_id)
        .order_by(Alert.created_at.desc())
        .all()
    )
