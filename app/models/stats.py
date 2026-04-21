from sqlalchemy import Column, Integer, Float, Boolean, Date, ForeignKey, Enum
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

    user = relationship("User", back_populates="stats")