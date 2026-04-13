"""
sales.py - Sales API Routes

Endpoints:
    POST /sales/add           - Add a new sales record
    GET  /sales/{product_id}  - Get sales history for a product
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from backend.db.database import get_db
from backend.db.models import Sales, Product
from backend.db.schemas import SalesCreate, SalesResponse

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/add", response_model=SalesResponse)
def add_sale(sale: SalesCreate, db: Session = Depends(get_db)):
    """
    Record a new sale.

    Args:
        sale: Product ID, date, and quantity sold
        db: Injected database session

    Returns:
        Created sales record

    Raises:
        404: If product doesn't exist
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == sale.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {sale.product_id} not found")

    db_sale = Sales(
        product_id=sale.product_id,
        date=sale.date,
        quantity_sold=sale.quantity_sold,
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


@router.get("/{product_id}", response_model=list[SalesResponse])
def get_sales(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve sales history for a specific product, ordered by date.

    Args:
        product_id: ID of the product

    Returns:
        List of sales records sorted by date
    """
    sales = (
        db.query(Sales)
        .filter(Sales.product_id == product_id)
        .order_by(Sales.date)
        .all()
    )
    return sales
