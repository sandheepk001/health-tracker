from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models.stats import UserStats
from app.models.user import User
from app.schemas.stats import StatsCreate, StatsOut
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.post("/log", response_model=StatsOut)
def log_stats(
    payload: StatsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(UserStats).filter(
        UserStats.user_id == current_user.id,
        UserStats.date == payload.date
    ).first()

    if existing:
        data = payload.model_dump(exclude_none=True)

        # if updating walk_km, clear steps and vice versa
        # so old value doesn't persist alongside new one
        if 'walk_km' in data and data['walk_km'] is not None:
            existing.steps = None
        if 'steps' in data and data['steps'] is not None:
            existing.walk_km = None

        # if gym_done is being set to False, clear gym details
        if 'gym_done' in data and data['gym_done'] is False:
            existing.gym_mins = None
            existing.gym_intensity = None

        for field, value in data.items():
            setattr(existing, field, value)

        db.commit()
        db.refresh(existing)
        return existing

    stats = UserStats(user_id=current_user.id, **payload.model_dump())
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats

@router.get("/weight/history", response_model=list[StatsOut])
def weight_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(UserStats).filter(
        UserStats.user_id == current_user.id,
        UserStats.weight_kg.isnot(None)
    ).order_by(UserStats.date.asc()).all()

@router.delete("/weight/{stat_id}")
def delete_weight_entry(
    stat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stat = db.query(UserStats).filter(
        UserStats.id == stat_id,
        UserStats.user_id == current_user.id
    ).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Entry not found")
    stat.weight_kg = None
    db.commit()
    return {"detail": "Weight entry removed"}

@router.get("/{log_date}", response_model=StatsOut)
def get_stats(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = db.query(UserStats).filter(
        UserStats.user_id == current_user.id,
        UserStats.date == log_date
    ).first()
    if not stats:
        raise HTTPException(status_code=404, detail="No stats found for this date")
    return stats

@router.get("/range/list", response_model=list[StatsOut])
def get_stats_range(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(UserStats).filter(
        UserStats.user_id == current_user.id,
        UserStats.date >= from_date,
        UserStats.date <= to_date
    ).order_by(UserStats.date).all()