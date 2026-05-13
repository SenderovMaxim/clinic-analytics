from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .db import get_db
from .queries import REVENUE_QUERY, REFERRAL_QUERY
from datetime import datetime

router = APIRouter()


@router.get("/api/analytics")
def get_analytics(
        start_date: str = Query(None, description="YYYY-MM-DD"),
        end_date: str = Query(None, description="YYYY-MM-DD"),
        db: Session = Depends(get_db)
):
    # Если даты не указаны, берем весь период
    s = start_date or "2000-01-01"
    e = end_date or datetime.now().strftime("%Y-%m-%d")

    try:
        revenue_rows = db.execute(REVENUE_QUERY, {"start_date": s, "end_date": e}).mappings().all()
        referral_rows = db.execute(REFERRAL_QUERY, {"start_date": s, "end_date": e}).mappings().all()

        return {
            "period": {"start": s, "end": e},
            "revenue": [dict(r) for r in revenue_rows],
            "referrals": [dict(r) for r in referral_rows]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {str(e)}")