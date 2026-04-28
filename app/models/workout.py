from sqlalchemy import Column, Integer, Float, Boolean, Date, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False)
    equipment = Column(String(30), nullable=True)
    is_custom = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sets = relationship("WorkoutSet", back_populates="exercise")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String(100), nullable=True)
    duration_mins = Column(Integer, nullable=True)
    intensity = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    is_rest_day = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sets = relationship("WorkoutSet", back_populates="session", cascade="all, delete")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("workout_exercises.id"), nullable=False)
    set_number = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    duration_secs = Column(Integer, nullable=True)
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("WorkoutSession", back_populates="sets")
    exercise = relationship("WorkoutExercise", back_populates="sets")