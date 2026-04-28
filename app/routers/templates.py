from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.models.meal_template import MealTemplate, MealTemplateItem
from app.models.food import Food
from app.models.food_log import FoodLog
from app.models.user import User
from app.core.dependencies import get_current_user
from datetime import date

router = APIRouter(prefix="/templates", tags=["Templates"])

class TemplateItemCreate(BaseModel):
    food_id: int
    quantity: float
    unit: str = "g"

class TemplateItemOut(BaseModel):
    id: int
    food_id: int
    food_name: Optional[str] = None
    quantity: float
    unit: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    class Config:
        from_attributes = True

class TemplateCreate(BaseModel):
    name: str
    meal_type: str
    items: List[TemplateItemCreate]

class TemplateOut(BaseModel):
    id: int
    name: str
    meal_type: str
    items: List[TemplateItemOut] = []
    total_calories: Optional[float] = None
    class Config:
        from_attributes = True

class LogTemplateRequest(BaseModel):
    date: date
    meal_type: str
    items: List[TemplateItemCreate]

def _enrich_items(items, db):
    result = []
    for item in items:
        food = db.query(Food).filter(Food.id == item.food_id).first()
        ratio = item.quantity / 100
        result.append({
            "id": item.id,
            "food_id": item.food_id,
            "food_name": food.name if food else None,
            "quantity": item.quantity,
            "unit": item.unit,
            "calories": round(food.calories_per_100g * ratio, 1) if food else None,
            "protein_g": round(food.protein_per_100g * ratio, 1) if food else None,
            "carbs_g": round(food.carbs_per_100g * ratio, 1) if food else None,
            "fat_g": round(food.fat_per_100g * ratio, 1) if food else None,
        })
    return result

@router.post("", response_model=TemplateOut)
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = MealTemplate(
        user_id=current_user.id,
        name=payload.name,
        meal_type=payload.meal_type
    )
    db.add(template)
    db.flush()

    for item in payload.items:
        db.add(MealTemplateItem(
            template_id=template.id,
            food_id=item.food_id,
            quantity=item.quantity,
            unit=item.unit
        ))
    db.commit()
    db.refresh(template)

    enriched = _enrich_items(template.items, db)
    total = sum(i["calories"] or 0 for i in enriched)
    return {**template.__dict__, "items": enriched, "total_calories": round(total, 1)}

@router.get("", response_model=list[TemplateOut])
def get_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    templates = db.query(MealTemplate).filter(
        MealTemplate.user_id == current_user.id
    ).order_by(MealTemplate.name).all()
    result = []
    for t in templates:
        enriched = _enrich_items(t.items, db)
        total = sum(i["calories"] or 0 for i in enriched)
        result.append({**t.__dict__, "items": enriched, "total_calories": round(total, 1)})
    return result

@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    t = db.query(MealTemplate).filter(
        MealTemplate.id == template_id,
        MealTemplate.user_id == current_user.id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(t)
    db.commit()
    return {"detail": "Deleted"}

@router.post("/log")
def log_template(
    payload: LogTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logged = []
    for item in payload.items:
        food = db.query(Food).filter(Food.id == item.food_id).first()
        if not food:
            continue
        ratio = item.quantity / 100
        log = FoodLog(
            user_id=current_user.id,
            food_id=item.food_id,
            date=payload.date,
            meal_type=payload.meal_type,
            quantity=item.quantity,
            unit=item.unit,
            calories=round(food.calories_per_100g * ratio, 2),
            protein_g=round(food.protein_per_100g * ratio, 2),
            carbs_g=round(food.carbs_per_100g * ratio, 2),
            fat_g=round(food.fat_per_100g * ratio, 2),
            fiber_g=round(food.fiber_per_100g * ratio, 2),
        )
        db.add(log)
        logged.append(food.name)
    db.commit()
    return {"detail": f"Logged {len(logged)} items.", "items": logged}