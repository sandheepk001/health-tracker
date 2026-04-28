from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.food import Food
from app.models.user import User
from app.schemas.food import FoodCreate, FoodOut
from app.core.dependencies import get_current_user
import httpx
import uuid

router = APIRouter(prefix="/foods", tags=["Foods"])

async def search_open_food_facts(query: str) -> list:
    url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10,
        "fields": "product_name,nutriments,serving_size"
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, params=params)
            data = r.json()
            results = []
            for p in data.get("products", []):
                name = p.get("product_name", "").strip()
                n = p.get("nutriments", {})
                cal = n.get("energy-kcal_100g") or n.get("energy_100g", 0)
                if not name or not cal:
                    continue
                results.append({
                    "id": str(uuid.uuid4()),  # ✓ FIX: Generate unique ID for OFF items
                    "name": name,
                    "unit": "g",
                    "calories_per_100g": round(float(cal), 1),
                    "protein_per_100g": round(float(n.get("proteins_100g", 0)), 1),
                    "carbs_per_100g": round(float(n.get("carbohydrates_100g", 0)), 1),
                    "fat_per_100g": round(float(n.get("fat_100g", 0)), 1),
                    "fiber_per_100g": round(float(n.get("fiber_100g", 0)), 1),
                    "created_by_user_id": None,
                    "created_at": None,
                    "from_off": True  # ✓ Flag it as OFF result
                })
            return results[:5]
    except Exception:
        return []

@router.get("/search")
async def search_food(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    tokens = q.strip().split()
    token_filters = [Food.name.ilike(f"%{token}%") for token in tokens]

    local_results = db.query(Food).filter(
        or_(*token_filters, func.similarity(Food.name, q) > 0.2)
    ).order_by(func.similarity(Food.name, q).desc()).limit(10).all()

    response = [
        {
            "id": f.id,
            "name": f.name,
            "unit": f.unit,
            "calories_per_100g": f.calories_per_100g,
            "protein_per_100g": f.protein_per_100g,
            "carbs_per_100g": f.carbs_per_100g,
            "fat_per_100g": f.fat_per_100g,
            "fiber_per_100g": f.fiber_per_100g,
            "created_by_user_id": f.created_by_user_id,
            "created_at": str(f.created_at),
            "from_off": False  # ✓ Local results are NOT from OFF
        }
        for f in local_results
    ]

    # if fewer than 3 local results, supplement with Open Food Facts
    if len(local_results) < 3:
        off_results = await search_open_food_facts(q)
        response.extend(off_results)

    return response

@router.post("", response_model=FoodOut)
def add_food(
    payload: FoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Food).filter(Food.name.ilike(payload.name)).first()
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