from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.body_measurement import BodyMeasurement
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/measurements", tags=["Measurements"])

MEASUREMENT_TYPES = [
    "waist", "chest", "hips",
    "left_arm", "right_arm",
    "left_thigh", "right_thigh",
    "neck", "body_fat_pct"
]

class MeasurementCreate(BaseModel):
    date: date
    measurement_type: str
    value_cm: Optional[float] = None
    body_fat_pct: Optional[float] = None
    notes: Optional[str] = None

class MeasurementOut(MeasurementCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

@router.post("", response_model=MeasurementOut)
def log_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.measurement_type not in MEASUREMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid measurement type. Valid: {MEASUREMENT_TYPES}")

    # update existing entry for same date + type
    existing = db.query(BodyMeasurement).filter(
        BodyMeasurement.user_id == current_user.id,
        BodyMeasurement.date == payload.date,
        BodyMeasurement.measurement_type == payload.measurement_type
    ).first()

    if existing:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    m = BodyMeasurement(user_id=current_user.id, **payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/history/{measurement_type}", response_model=list[MeasurementOut])
def get_measurement_history(
    measurement_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(BodyMeasurement).filter(
        BodyMeasurement.user_id == current_user.id,
        BodyMeasurement.measurement_type == measurement_type
    ).order_by(BodyMeasurement.date.asc()).all()

@router.get("/latest", response_model=list[MeasurementOut])
def get_latest_measurements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # get latest entry per measurement type
    subq = db.query(
        BodyMeasurement.measurement_type,
        func.max(BodyMeasurement.date).label("max_date")
    ).filter(
        BodyMeasurement.user_id == current_user.id
    ).group_by(BodyMeasurement.measurement_type).subquery()

    return db.query(BodyMeasurement).join(
        subq,
        (BodyMeasurement.measurement_type == subq.c.measurement_type) &
        (BodyMeasurement.date == subq.c.max_date)
    ).filter(BodyMeasurement.user_id == current_user.id).all()

@router.delete("/{measurement_id}")
def delete_measurement(
    measurement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    m = db.query(BodyMeasurement).filter(
        BodyMeasurement.id == measurement_id,
        BodyMeasurement.user_id == current_user.id
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Measurement not found")
    db.delete(m)
    db.commit()
    return {"detail": "Deleted"}