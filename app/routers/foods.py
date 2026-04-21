from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.food import Food
from app.models.user import User
from app.schemas.food import FoodCreate, FoodOut
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/foods", tags=["Foods"])

@router.get("/search", response_model=list[FoodOut])
def search_food(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    # split into tokens so "chicken rice" matches both words independently
    tokens = q.strip().split()

    # build a filter: each token must appear somewhere in the name
    token_filters = [Food.name.ilike(f"%{token}%") for token in tokens]

    # also add full fuzzy similarity match using pg_trgm
    results = db.query(Food).filter(
        or_(
            *token_filters,
            func.similarity(Food.name, q) > 0.2
        )
    ).order_by(
        func.similarity(Food.name, q).desc()
    ).limit(20).all()

    return results

@router.post("", response_model=FoodOut)
def add_food(
    payload: FoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Food).filter(
        Food.name.ilike(payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Food already exists in database")

    food = Food(**payload.model_dump(), created_by_user_id=current_user.id)
    db.add(food)
    db.commit()
    db.refresh(food)
    return food

@router.get("/{food_id}", response_model=FoodOut)
def get_food(
    food_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return food