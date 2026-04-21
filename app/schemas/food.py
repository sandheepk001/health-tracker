from pydantic import BaseModel
from typing import Optional
from datetime import datetime

VALID_UNITS = ["g", "ml", "piece", "cup", "tbsp", "tsp", "scoop"]

class FoodCreate(BaseModel):
    name: str
    unit: str = "g"
    calories_per_100g: float
    protein_per_100g: float = 0.0
    carbs_per_100g: float = 0.0
    fat_per_100g: float = 0.0
    fiber_per_100g: float = 0.0

class FoodOut(FoodCreate):
    id: int
    created_by_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True