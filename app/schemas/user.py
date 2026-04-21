from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

class GenderEnum(str, Enum):
    male = "male"
    female = "female"

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    gender: GenderEnum
    age: int
    height_cm: float
    initial_weight: Optional[float] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    gender: GenderEnum
    age: int
    height_cm: float
    initial_weight: Optional[float] = None
    target_protein: Optional[float] = None
    target_carbs: Optional[float] = None
    target_fat: Optional[float] = None
    target_fiber: Optional[float] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    initial_weight: Optional[float] = None
    target_protein: Optional[float] = None
    target_carbs: Optional[float] = None
    target_fat: Optional[float] = None
    target_fiber: Optional[float] = None