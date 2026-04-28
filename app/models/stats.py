from sqlalchemy import Column, Integer, Float, Boolean, Date, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class IntensityEnum(str, enum.Enum):
    light = "light"
    moderate = "moderate"
    intense = "intense"

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=True)
    walk_km = Column(Float, nullable=True)
    steps = Column(Integer, nullable=True)
    gym_done = Column(Boolean, default=False)
    gym_mins = Column(Integer, nullable=True)
    gym_intensity = Column(Enum(IntensityEnum, schema="public"), nullable=True)
    is_fasting = Column(Boolean, default=False)
    water_ml = Column(Float, default=0)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(String(20), nullable=True)
    is_rest_day = Column(Boolean, default=False)
    rest_day_reason = Column(String(50), nullable=True)
    mood = Column(String(20), nullable=True)

    user = relationship("User", back_populates="stats")