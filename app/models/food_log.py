from sqlalchemy import Column, Integer, Float, Date, ForeignKey, Enum, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class MealTypeEnum(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"

class FoodLog(Base):
    __tablename__ = "food_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("food_db.id"), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(Enum(MealTypeEnum, schema="public"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, default="g", nullable=False)

    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="food_logs")
    food = relationship("Food", back_populates="logs")