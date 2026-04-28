from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.models.user import User
from app.models.stats import UserStats
from app.models.food_log import FoodLog
from app.core.dependencies import get_current_user
from app.routers.summary import compute_daily

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/streaks")
def get_streaks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    last_streak_date = None

    # check last 365 days
    for i in range(365):
        check_date = today - timedelta(days=i)

        # check if food was logged
        food_logged = db.query(FoodLog).filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date == check_date
        ).first()

        # check if stats were logged
        stats_logged = db.query(UserStats).filter(
            UserStats.user_id == current_user.id,
            UserStats.date == check_date
        ).first()

        # fasting counts as food logged
        is_fasting = stats_logged and stats_logged.is_fasting
        day_logged = (food_logged or is_fasting) and stats_logged

        if day_logged:
            if i == 0 or last_streak_date == check_date + timedelta(days=1):
                temp_streak += 1
                last_streak_date = check_date
                if i == 0 or current_streak == temp_streak - 1:
                    current_streak = temp_streak
            else:
                temp_streak = 1
                last_streak_date = check_date
            longest_streak = max(longest_streak, temp_streak)
        else:
            if i > 0:
                temp_streak = 0

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "today_logged": current_streak > 0 and (
            db.query(FoodLog).filter(
                FoodLog.user_id == current_user.id,
                FoodLog.date == today
            ).first() is not None
        )
    }


@router.get("/macros")
def macro_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    today = date.today()
    days_back = 14  # analyse last 2 weeks

    summaries = []
    for i in range(days_back):
        d = today - timedelta(days=i)
        s = compute_daily(current_user.id, d, db)
        if s["total_calories"] > 0:
            summaries.append(s)

    if not summaries:
        return {
            "days_analysed": 0,
            "message": "No food logs found in the last 14 days.",
            "macros": {}
        }

    targets = {
        "protein": user.target_protein,
        "carbs": user.target_carbs,
        "fat": user.target_fat,
        "fiber": user.target_fiber,
    }

    fields = {
        "protein": "total_protein_g",
        "carbs": "total_carbs_g",
        "fat": "total_fat_g",
        "fiber": "total_fiber_g",
    }

    result = {}
    suggestions = []

    for macro, field in fields.items():
        values = [s[field] for s in summaries if s[field] is not None]
        avg = round(sum(values) / len(values), 1) if values else 0
        target = targets[macro]

        hit_rate = None
        gap = None
        status = "no_target"

        if target:
            hits = sum(1 for v in values if v >= target * 0.9)
            hit_rate = round((hits / len(values)) * 100, 1)
            gap = round(avg - target, 1)
            if hit_rate < 50:
                status = "under"
            elif hit_rate >= 80:
                status = "on_track"
            else:
                status = "inconsistent"

            # generate suggestions
            if macro == "protein" and gap < -10:
                suggestions.append(
                    f"You're averaging {abs(gap)}g below your protein target. "
                    f"Try adding eggs, paneer, chicken, or dal to your meals."
                )
            elif macro == "fiber" and gap < -5:
                suggestions.append(
                    f"Fiber intake is low — {abs(gap)}g below target on average. "
                    f"Add vegetables, fruits, or whole grains."
                )
            elif macro == "fat" and gap > 15:
                suggestions.append(
                    f"Fat intake is running {gap}g above target on average. "
                    f"Check cooking oils, nuts, and dairy portions."
                )
            elif macro == "carbs" and gap > 30:
                suggestions.append(
                    f"Carb intake is {gap}g above target on average. "
                    f"Consider reducing rice, bread, or sugar intake."
                )

        result[macro] = {
            "avg": avg,
            "target": target,
            "hit_rate_pct": hit_rate,
            "gap": gap,
            "status": status,
        }

    # protein-specific insight even without target
    if not targets["protein"]:
        avg_protein = result["protein"]["avg"]
        weight = db.query(UserStats).filter(
            UserStats.user_id == current_user.id,
            UserStats.weight_kg.isnot(None)
        ).order_by(UserStats.date.desc()).first()
        if weight:
            recommended = round(weight.weight_kg * 1.6, 0)
            if avg_protein < recommended * 0.8:
                suggestions.append(
                    f"Based on your weight, recommended protein is ~{recommended}g/day. "
                    f"You're averaging {avg_protein}g. Consider setting a protein target."
                )

    return {
        "days_analysed": len(summaries),
        "macros": result,
        "suggestions": suggestions
    }


@router.get("/plateau")
def plateau_detection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    two_weeks_ago = today - timedelta(days=14)

    weights = db.query(UserStats).filter(
        UserStats.user_id == current_user.id,
        UserStats.weight_kg.isnot(None),
        UserStats.date >= two_weeks_ago
    ).order_by(UserStats.date.asc()).all()

    if len(weights) < 4:
        return {
            "plateau_detected": False,
            "message": "Not enough weight data in the last 2 weeks to detect plateau.",
            "data_points": len(weights)
        }

    first_w = weights[0].weight_kg
    last_w = weights[-1].weight_kg
    change = abs(last_w - first_w)

    # check if there's a consistent deficit
    deficits = []
    for i in range(14):
        d = today - timedelta(days=i)
        s = compute_daily(current_user.id, d, db)
        if s.get("deficit") and s["deficit"] > 0:
            deficits.append(s["deficit"])

    avg_deficit = round(sum(deficits) / len(deficits), 1) if deficits else 0
    plateau = change < 0.5 and avg_deficit > 200

    suggestions = []
    if plateau:
        suggestions = [
            "Your weight hasn't changed significantly despite a consistent deficit. This is normal after several weeks.",
            "Try adjusting your calorie intake by 100-200 kcal downward.",
            "Consider varying your workout intensity or adding a new activity.",
            "Check if you've been logging accurately — portion sizes can drift over time.",
        ]

    return {
        "plateau_detected": plateau,
        "weight_change_2w": round(last_w - first_w, 2),
        "avg_daily_deficit": avg_deficit,
        "deficit_days": len(deficits),
        "first_weight": first_w,
        "last_weight": last_w,
        "message": "Plateau detected — see suggestions below." if plateau else
                   "No plateau detected. Weight is responding to your deficit." if avg_deficit > 200 else
                   "Log more consistently to enable plateau detection.",
        "suggestions": suggestions
    }