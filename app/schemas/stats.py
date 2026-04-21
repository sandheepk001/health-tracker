from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional

class IntensityEnum(str, Enum):
    light = "light"
    moderate = "moderate"
    intense = "intense"

class StatsCreate(BaseModel):
    date: date
    weight_kg: Optional[float] = None
    walk_km: Optional[float] = None
    steps: Optional[int] = None
    gym_done: bool = False
    gym_mins: Optional[int] = None
    gym_intensity: Optional[IntensityEnum] = None
    is_fasting: bool = False

class StatsOut(StatsCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True