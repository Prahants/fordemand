"""
qr_codes.py - QR Code metadata API routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import QRCodeEntry
from backend.db.schemas import QRCodeCreate, QRCodeResponse
from backend.services.auth import require_role

router = APIRouter(prefix="/qr-codes", tags=["QR Codes"])


@router.post("/", response_model=QRCodeResponse)
def create_qr_code(
    qr_data: QRCodeCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    entry = QRCodeEntry(
        product=qr_data.product,
        sku=qr_data.sku,
        category=qr_data.category,
        price=qr_data.price,
        qr_payload=qr_data.qr_payload,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[QRCodeResponse])
def list_qr_codes(
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    return db.query(QRCodeEntry).order_by(QRCodeEntry.created_at.desc()).all()
