"""
inventory.py - Inventory API Routes

Endpoints:
    GET  /inventory        - List all inventory records
    POST /inventory/update - Update stock for a product
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.schemas import InventoryUpdate, InventoryResponse
from backend.services.inventory_service import update_inventory_stock, get_all_inventory
from backend.services.auth import require_role

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/", response_model=list[InventoryResponse])
def get_inventory(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    """
    Retrieve all inventory records with product names.

    Returns:
        List of inventory records including stock levels and reorder thresholds
    """
    return get_all_inventory(db)


@router.post("/update", response_model=InventoryResponse)
def update_inventory(
    update: InventoryUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    """
    Update or create inventory record for a product.

    Args:
        update: Product ID, new stock level, and optional reorder threshold
        db: Injected database session

    Returns:
        Updated inventory record
    """
    inventory = update_inventory_stock(
        db=db,
        product_id=update.product_id,
        store_id=update.store_id,
        stock=update.stock,
        reorder_threshold=update.reorder_threshold,
    )
    return inventory
