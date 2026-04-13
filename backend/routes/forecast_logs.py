"""
forecast_logs.py - Routes for forecast variance tracking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import ForecastLog
from backend.db.schemas import ForecastLogResponse
from backend.services.auth import require_role

router = APIRouter(prefix="/forecast-logs", tags=["Forecast Logs"])


@router.get("/", response_model=list[ForecastLogResponse])
def list_forecast_logs(
    product_id: int | None = None,
    store_id: int | None = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_role({"admin", "manager", "staff"})),
):
    query = db.query(ForecastLog).order_by(ForecastLog.generated_at.desc())
    if product_id is not None:
        query = query.filter(ForecastLog.product_id == product_id)
    if store_id is not None:
        query = query.filter(ForecastLog.store_id == store_id)
    return query.limit(200).all()
