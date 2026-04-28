from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.database import get_db
from app.models.food_log import FoodLog
from app.models.stats import UserStats
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/summary", tags=["Summary"])

MET = { "light": 3.0, "moderate": 5.0, "intense": 8.0 }

def calc_bmr(weight, height, age, gender):
    base = 10 * weight + 6.25 * height - 5 * age
    return base + 5 if gender == "male" else base - 161

def calc_activity_cals(weight, walk_km, steps, gym_done, gym_mins, gym_intensity, height_cm=None):
    effective_km = walk_km
    if not effective_km and steps:
        # use height-based step length if available, else fall back to average
        if height_cm:
            step_length_km = (height_cm * 0.413) / 100000
        else:
            step_length_km = 0.000762
        effective_km = steps * step_length_km

    walk_cals = weight * (effective_km or 0) * 0.9
    gym_cals = 0
    if gym_done and gym_mins and gym_intensity:
        met = MET.get(gym_intensity.value if hasattr(gym_intensity, 'value') else gym_intensity, 5.0)
        gym_cals = met * weight * (gym_mins / 60)
    return round(walk_cals, 2), round(gym_cals, 2)

def compute_daily(user_id: int, log_date: date, db: Session):
    logs = db.query(FoodLog).filter(
        FoodLog.user_id == user_id,
        FoodLog.date == log_date
    ).all()

    stats = db.query(UserStats).filter(
        UserStats.user_id == user_id,
        UserStats.date == log_date
    ).first()

    user = db.query(User).filter(User.id == user_id).first()

    total_calories = round(sum(l.calories for l in logs), 2)
    total_protein  = round(sum(l.protein_g for l in logs), 2)
    total_carbs    = round(sum(l.carbs_g for l in logs), 2)
    total_fat      = round(sum(l.fat_g for l in logs), 2)
    total_fiber    = round(sum(l.fiber_g for l in logs), 2)

    tdee = None
    bmr = None
    walk_cals = None
    gym_cals = None
    deficit = None
    effective_km = None
    is_fasting = stats.is_fasting if stats else False

    if stats and user:
        # use logged weight, fall back to latest available weight
        weight = stats.weight_kg
        if not weight:
            latest = db.query(UserStats).filter(
                UserStats.user_id == user_id,
                UserStats.weight_kg.isnot(None),
                UserStats.date <= log_date
            ).order_by(UserStats.date.desc()).first()
            weight = latest.weight_kg if latest else None

        if weight:
            if stats.walk_km:
                effective_km = stats.walk_km
            elif stats.steps:
                step_length_km = (user.height_cm * 0.413) / 100000
                effective_km = round(stats.steps * step_length_km, 2)

            bmr = round(calc_bmr(weight, user.height_cm, user.age, user.gender), 2)
            walk_cals, gym_cals = calc_activity_cals(
                weight,
                stats.walk_km,
                stats.steps,
                stats.gym_done,
                stats.gym_mins,
                stats.gym_intensity,
                user.height_cm
            )
            tdee = round(bmr + walk_cals + gym_cals, 2)
            if total_calories > 0:
                deficit = round(tdee - total_calories, 2)

    return {
        "date": log_date,
        "is_fasting": is_fasting,
        "total_calories": 0 if is_fasting else total_calories,
        "total_protein_g": 0 if is_fasting else total_protein,
        "total_carbs_g": 0 if is_fasting else total_carbs,
        "total_fat_g": 0 if is_fasting else total_fat,
        "total_fiber_g": 0 if is_fasting else total_fiber,
        "stats_logged": stats is not None,
        "weight_kg": stats.weight_kg if stats else None,
        "walk_km": effective_km,
        "steps": stats.steps if stats else None,
        "water_ml": stats.water_ml if stats else 0,
        "sleep_hours": stats.sleep_hours if stats else None,
        "sleep_quality": stats.sleep_quality if stats else None,
        "is_rest_day": stats.is_rest_day if stats else False,
        "rest_day_reason": stats.rest_day_reason if stats else None,
        "mood": stats.mood if stats else None,
        "gym_done": stats.gym_done if stats else None,
        "gym_mins": stats.gym_mins if stats else None,
        "gym_intensity": stats.gym_intensity if stats else None,
        "bmr": bmr,
        "walk_cals": walk_cals,
        "gym_cals": gym_cals,
        "tdee": tdee,
        "deficit": round(tdee, 2) if is_fasting and tdee else deficit,
    }


@router.get("/daily/{log_date}")
def daily_summary(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return compute_daily(current_user.id, log_date, db)

@router.get("/weekly")
def weekly_summary(
    week_start: date,
    override_calories: float | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    days = [week_start + timedelta(days=i) for i in range(7)]
    summaries = [compute_daily(current_user.id, d, db) for d in days]
    logged_days = [s for s in summaries if s["total_calories"] > 0]
    avg_calories = round(
        sum(s["total_calories"] for s in logged_days) / len(logged_days), 2
    ) if logged_days else 0

    return {
        "week_start": week_start,
        "days_logged": len(logged_days),
        "avg_daily_calories": avg_calories,
        "effective_calories": override_calories if override_calories else avg_calories,
        "overridden": override_calories is not None,
        "daily_breakdown": summaries
    }