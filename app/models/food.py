from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Food(Base):
    __tablename__ = "food_db"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    unit = Column(String, default="g", nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, default=0.0)
    carbs_per_100g = Column(Float, default=0.0)
    fat_per_100g = Column(Float, default=0.0)
    fiber_per_100g = Column(Float, default=0.0)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    logs = relationship("FoodLog", back_populates="food")