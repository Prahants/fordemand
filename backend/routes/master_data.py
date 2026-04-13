"""
master_data.py - Setup routes for stores, suppliers, and users.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Store, Supplier, User
from backend.db.schemas import (
    StoreCreate,
    StoreResponse,
    SupplierCreate,
    SupplierResponse,
    UserResponse,
)
from backend.services.auth import require_role

router = APIRouter(prefix="/master", tags=["Master Data"])


@router.post("/stores", response_model=StoreResponse)
def create_store(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin"})),
):
    store = Store(name=payload.name, location=payload.location, store_type=payload.store_type)
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("/stores", response_model=list[StoreResponse])
def list_stores(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    return db.query(Store).all()


@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager"})),
):
    supplier = Supplier(
        name=payload.name,
        contact_email=payload.contact_email,
        phone=payload.phone,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager"})),
):
    return db.query(Supplier).all()


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager"})),
):
    return db.query(User).all()
