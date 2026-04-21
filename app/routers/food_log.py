from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models.food_log import FoodLog
from app.models.food import Food
from app.models.user import User
from app.schemas.food_log import FoodLogCreate, FoodLogOut
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/food-log", tags=["Food Log"])

@router.post("", response_model=FoodLogOut)
def log_food(
    payload: FoodLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    food = db.query(Food).filter(Food.id == payload.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    ratio = payload.quantity / 100

    log = FoodLog(
        user_id=current_user.id,
        food_id=payload.food_id,
        date=payload.date,
        meal_type=payload.meal_type,
        quantity=payload.quantity,
        unit=payload.unit or food.unit,
        calories=round(food.calories_per_100g * ratio, 2),
        protein_g=round(food.protein_per_100g * ratio, 2),
        carbs_g=round(food.carbs_per_100g * ratio, 2),
        fat_g=round(food.fat_per_100g * ratio, 2),
        fiber_g=round(food.fiber_per_100g * ratio, 2),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.get("/{log_date}", response_model=list[FoodLogOut])
def get_food_log(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(FoodLog).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.date == log_date
    ).order_by(FoodLog.meal_type).all()

@router.delete("/{log_id}")
def delete_food_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(FoodLog).filter(
        FoodLog.id == log_id,
        FoodLog.user_id == current_user.id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    db.delete(log)
    db.commit()
    return {"detail": "Deleted successfully"}