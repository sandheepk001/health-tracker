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

    # only update fields that were explicitly provided in the request
    # exclude_unset=True means only fields the caller actually sent
    data = payload.model_dump(exclude_unset=True)
    data.pop('date', None)

    if existing:
        # if updating walk_km clear steps and vice versa
        if 'walk_km' in data and data['walk_km'] is not None:
            existing.steps = None
        if 'steps' in data and data['steps'] is not None:
            existing.walk_km = None

        # if gym_done is being set to False clear gym details
        if data.get('gym_done') is False:
            existing.gym_mins = None
            existing.gym_intensity = None

        for field, value in data.items():
            setattr(existing, field, value)

        db.commit()
        db.refresh(existing)
        return existing

    # new entry — set defaults for unset fields
    new_stats = UserStats(
        user_id=current_user.id,
        date=payload.date,
        weight_kg=data.get('weight_kg'),
        walk_km=data.get('walk_km'),
        steps=data.get('steps'),
        gym_done=data.get('gym_done', False),
        gym_mins=data.get('gym_mins'),
        gym_intensity=data.get('gym_intensity'),
        is_fasting=data.get('is_fasting', False)
    )
    db.add(new_stats)
    db.commit()
    db.refresh(new_stats)
    return new_stats

@router.get("/weight/history", response_model=list[StatsOut])
def weight_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(UserStats).filter(
        UserStats.user_id == current_user.id,
        UserStats.weight_kg.isnot(None)
    ).order_by(UserStats.date.asc()).all()

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