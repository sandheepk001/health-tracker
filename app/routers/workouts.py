from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.models.workout import WorkoutExercise, WorkoutSession, WorkoutSet
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/workout", tags=["Workout"])

# ── schemas ──────────────────────────────────────────────────────

class ExerciseOut(BaseModel):
    id: int
    name: str
    category: str
    equipment: Optional[str] = None
    is_custom: bool
    class Config:
        from_attributes = True

class SetCreate(BaseModel):
    exercise_id: int
    set_number: int
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_secs: Optional[int] = None
    notes: Optional[str] = None

class SetOut(SetCreate):
    id: int
    session_id: int
    exercise_name: Optional[str] = None
    exercise_category: Optional[str] = None
    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    date: date
    name: Optional[str] = None
    duration_mins: Optional[int] = None
    intensity: Optional[str] = None
    notes: Optional[str] = None
    is_rest_day: bool = False

class SessionOut(BaseModel):
    id: int
    user_id: int
    date: date
    name: Optional[str] = None
    duration_mins: Optional[int] = None
    intensity: Optional[str] = None
    notes: Optional[str] = None
    is_rest_day: bool
    sets: List[SetOut] = []
    class Config:
        from_attributes = True

class CustomExerciseCreate(BaseModel):
    name: str
    category: str
    equipment: Optional[str] = None

# ── exercises ────────────────────────────────────────────────────

@router.get("/exercises", response_model=list[ExerciseOut])
def get_exercises(
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WorkoutExercise).filter(
        (WorkoutExercise.is_custom == False) |
        (WorkoutExercise.created_by_user_id == current_user.id)
    )
    if category:
        query = query.filter(WorkoutExercise.category == category)
    if q:
        query = query.filter(WorkoutExercise.name.ilike(f"%{q}%"))
    return query.order_by(WorkoutExercise.category, WorkoutExercise.name).all()

@router.post("/exercises", response_model=ExerciseOut)
def create_custom_exercise(
    payload: CustomExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ex = WorkoutExercise(
        name=payload.name,
        category=payload.category,
        equipment=payload.equipment,
        is_custom=True,
        created_by_user_id=current_user.id
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex

# ── sessions ─────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionOut)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = WorkoutSession(user_id=current_user.id, **payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_with_sets(session, db)

@router.get("/sessions/{session_date}", response_model=list[SessionOut])
def get_sessions_by_date(
    session_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.date == session_date
    ).all()
    return [_session_with_sets(s, db) for s in sessions]

@router.get("/sessions/range/list", response_model=list[SessionOut])
def get_sessions_range(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.date >= from_date,
        WorkoutSession.date <= to_date
    ).order_by(WorkoutSession.date.desc()).all()
    return [_session_with_sets(s, db) for s in sessions]

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(WorkoutSession).filter(
        WorkoutSession.id == session_id,
        WorkoutSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"detail": "Deleted"}

# ── sets ─────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/sets", response_model=SetOut)
def add_set(
    session_id: int,
    payload: SetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(WorkoutSession).filter(
        WorkoutSession.id == session_id,
        WorkoutSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    s = WorkoutSet(session_id=session_id, **payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _set_with_exercise(s, db)

@router.delete("/sets/{set_id}")
def delete_set(
    set_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = db.query(WorkoutSet).filter(WorkoutSet.id == set_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    db.delete(s)
    db.commit()
    return {"detail": "Deleted"}

# ── helpers ──────────────────────────────────────────────────────

def _set_with_exercise(s: WorkoutSet, db: Session) -> dict:
    ex = db.query(WorkoutExercise).filter(WorkoutExercise.id == s.exercise_id).first()
    return {
        "id": s.id,
        "session_id": s.session_id,
        "exercise_id": s.exercise_id,
        "set_number": s.set_number,
        "reps": s.reps,
        "weight_kg": s.weight_kg,
        "duration_secs": s.duration_secs,
        "notes": s.notes,
        "exercise_name": ex.name if ex else None,
        "exercise_category": ex.category if ex else None,
    }

def _session_with_sets(session: WorkoutSession, db: Session) -> dict:
    sets = db.query(WorkoutSet).filter(
        WorkoutSet.session_id == session.id
    ).order_by(WorkoutSet.set_number).all()
    return {
        "id": session.id,
        "user_id": session.user_id,
        "date": session.date,
        "name": session.name,
        "duration_mins": session.duration_mins,
        "intensity": session.intensity,
        "notes": session.notes,
        "is_rest_day": session.is_rest_day,
        "sets": [_set_with_exercise(s, db) for s in sets],
    }