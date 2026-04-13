"""
inventory_service.py - Business Logic for Inventory Management

Implements:
- Safety Stock calculation: Z * std_dev * sqrt(lead_time)
- Reorder Point calculation: (Forecasted Demand * lead_time) + Safety Stock
- Configurable lead time and service level (Z-score)
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.db.models import Inventory, Product


# ─── Default Configuration ────────────────────────────────────────
DEFAULT_LEAD_TIME = 3  # days
DEFAULT_Z_SCORE = 1.65  # 95% service level


def calculate_safety_stock(
    std_dev: float,
    lead_time: int = DEFAULT_LEAD_TIME,
    z_score: float = DEFAULT_Z_SCORE,
) -> float:
    """
    Calculate Safety Stock to buffer against demand variability.

    Formula: Safety Stock = Z * std_dev * sqrt(lead_time)

    Args:
        std_dev: Standard deviation of daily demand
        lead_time: Number of days for replenishment (default: 3)
        z_score: Service level Z-score (default: 1.65 for 95%)

    Returns:
        Safety stock quantity (float)
    """
    safety_stock = z_score * std_dev * np.sqrt(lead_time)
    return round(safety_stock, 2)


def calculate_reorder_point(
    forecasted_demand: float,
    lead_time: int = DEFAULT_LEAD_TIME,
    safety_stock: float = 0.0,
) -> float:
    """
    Calculate Reorder Point — the stock level at which a new order should be placed.

    Formula: Reorder Point = (Forecasted Demand * Lead Time) + Safety Stock

    Args:
        forecasted_demand: Average daily forecasted demand
        lead_time: Number of days for replenishment
        safety_stock: Calculated safety stock buffer

    Returns:
        Reorder point quantity (float)
    """
    reorder_point = (forecasted_demand * lead_time) + safety_stock
    return round(reorder_point, 2)


def update_inventory_stock(
    db: Session,
    product_id: int,
    stock: int,
    reorder_threshold: int = None,
) -> Inventory:
    """
    Update or create inventory record for a product.

    Args:
        db: Database session
        product_id: ID of the product
        stock: New stock level
        reorder_threshold: Optional new reorder threshold

    Returns:
        Updated Inventory ORM object
    """
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()

    if inventory:
        # Update existing inventory
        inventory.stock = stock
        if reorder_threshold is not None:
            inventory.reorder_threshold = reorder_threshold
        inventory.last_updated = datetime.now(timezone.utc)
    else:
        # Create new inventory record
        inventory = Inventory(
            product_id=product_id,
            stock=stock,
            reorder_threshold=reorder_threshold or 10,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(inventory)

    db.commit()
    db.refresh(inventory)
    return inventory


def get_all_inventory(db: Session) -> list:
    """
    Retrieve all inventory records with product names.

    Returns:
        List of dicts with inventory data and product names
    """
    results = (
        db.query(Inventory, Product.name)
        .join(Product, Inventory.product_id == Product.id)
        .all()
    )

    inventory_list = []
    for inv, product_name in results:
        inventory_list.append({
            "id": inv.id,
            "product_id": inv.product_id,
            "stock": inv.stock,
            "reorder_threshold": inv.reorder_threshold,
            "last_updated": inv.last_updated,
            "product_name": product_name,
        })
    return inventory_list
