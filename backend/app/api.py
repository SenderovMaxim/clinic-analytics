from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .db import get_db
from .queries import get_revenue_data, get_referral_data

router = APIRouter()


@router.get("/api/analytics")
def get_analytics(
        start_date: str = Query(...),
        end_date: str = Query(...),
        db: Session = Depends(get_db)
):
    revenue_rows = get_revenue_data(db, start_date, end_date)
    referral_rows = get_referral_data(db, start_date, end_date)

    return {
        "period": {"start": start_date, "end": end_date},
        "revenue": [
            {
                "doctor_id": row.doctor_id,
                "doctor_name": row.doctor_name,
                "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
                "total_procedures": row.total_procedures,
                "patient_count": row.patient_count
            }
            for row in revenue_rows
        ],
        "referrals": [
            {
                "doctor_id": row.doctor_id,
                "doctor_name": row.doctor_name,
                "total_patients": row.total_patients,
                "referred_patients": row.referred_patients,
                "referral_rate_pct": float(row.referral_rate_pct) if row.referral_rate_pct else 0
            }
            for row in referral_rows
        ]
    }