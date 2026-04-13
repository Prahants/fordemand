"""
products.py - Product API Routes

Endpoints:
    POST /products     - Create a new product
    GET  /products     - List all products
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Product
from backend.db.schemas import ProductCreate, ProductResponse
from backend.services.auth import require_role

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager"})),
):
    """
    Create a new product in the catalog.

    Args:
        product: Product name and category
        db: Injected database session

    Returns:
        Created product record
    """
    db_product = Product(
        name=product.name,
        category=product.category,
        sku=product.sku,
        supplier_id=product.supplier_id,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/", response_model=list[ProductResponse])
def get_all_products(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    """
    Retrieve all products from the catalog.

    Returns:
        List of all product records
    """
    return db.query(Product).all()


