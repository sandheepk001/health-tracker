from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    gender = Column(Enum(GenderEnum, schema="public"), nullable=False)
    age = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    initial_weight = Column(Float, nullable=True)
    target_protein = Column(Float, nullable=True)
    target_carbs = Column(Float, nullable=True)
    target_fat = Column(Float, nullable=True)
    target_fiber = Column(Float, nullable=True)
    daily_calorie_goal = Column(Float, nullable=True)
    daily_water_goal = Column(Float, default=2500)
    daily_steps_goal = Column(Integer, default=10000)

    stats = relationship("UserStats", back_populates="user")
    food_logs = relationship("FoodLog", back_populates="user")