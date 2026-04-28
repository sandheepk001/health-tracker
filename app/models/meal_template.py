from sqlalchemy import Column, Integer, Float, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class MealTemplate(Base):
    __tablename__ = "meal_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    meal_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("MealTemplateItem", back_populates="template", cascade="all, delete")
    user = relationship("User")

class MealTemplateItem(Base):
    __tablename__ = "meal_template_items"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("meal_templates.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("food_db.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default="g")

    template = relationship("MealTemplate", back_populates="items")
    food = relationship("Food")