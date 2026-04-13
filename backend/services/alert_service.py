"""
alert_service.py - Alert Generation Service

Checks inventory levels against calculated reorder points
and generates alerts when stock falls below the threshold.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.db.models import Alert, Product, Store


def check_and_create_alerts(
    db: Session,
    product_id: int,
    store_id: int,
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
        store = db.query(Store).filter(Store.id == store_id).first()
        store_name = store.name if store else f"Store #{store_id}"

        existing_open = (
            db.query(Alert)
            .filter(
                Alert.product_id == product_id,
                Alert.store_id == store_id,
                Alert.status == "open",
            )
            .first()
        )
        if existing_open:
            return existing_open

        message = (
            f"⚠️ LOW STOCK ALERT: '{product_name}' at '{store_name}' has {current_stock} units. "
            f"Reorder point is {reorder_point:.0f} units. Restock immediately!"
        )

        alert = Alert(
            product_id=product_id,
            store_id=store_id,
            message=message,
            status="open",
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
        db.query(Alert, Product.name, Store.name)
        .join(Product, Alert.product_id == Product.id)
        .join(Store, Alert.store_id == Store.id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    alerts_list = []
    for alert, product_name, store_name in results:
        alerts_list.append({
            "id": alert.id,
            "product_id": alert.product_id,
            "store_id": alert.store_id,
            "message": alert.message,
            "status": alert.status,
            "created_at": alert.created_at,
            "product_name": product_name,
            "store_name": store_name,
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
