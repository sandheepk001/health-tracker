from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum
from typing import Optional

class MealTypeEnum(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"

class FoodLogCreate(BaseModel):
    food_id: int
    date: date
    meal_type: MealTypeEnum
    quantity: float
    unit: str = "g"

class FoodLogOut(BaseModel):
    id: int
    user_id: int
    food_id: int
    date: date
    meal_type: MealTypeEnum
    quantity: float
    unit: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    created_at: datetime

    class Config:
        from_attributes = True