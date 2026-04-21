from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserOut
from app.core.security import hash_password, verify_password, create_access_token
from app.services.otp import (
    generate_otp, store_registration_otp,
    get_registration_data, clear_registration_data,
    verify_otp, get_otp_ttl
)
from app.services.email import send_otp_email

router = APIRouter(prefix="/auth", tags=["Auth"])

class SendRegisterOTPRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    gender: str
    age: int
    height_cm: float
    initial_weight: Optional[float] = None

class VerifyRegisterOTPRequest(BaseModel):
    email: EmailStr
    otp: str


@router.post("/register/send-otp")
def register_send_otp(
    payload: SendRegisterOTPRequest,
    db: Session = Depends(get_db)
):
    # check if email already registered
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # store registration data + otp in redis
    otp = generate_otp()
    registration_data = {
        "email": payload.email,
        "password": payload.password,
        "name": payload.name,
        "gender": payload.gender,
        "age": payload.age,
        "height_cm": payload.height_cm,
        "initial_weight": payload.initial_weight
    }
    store_registration_otp(payload.email, otp, registration_data)
    send_otp_email(payload.email, otp, payload.name)

    return {
        "detail": "OTP sent to your email.",
        "expires_in": get_otp_ttl(payload.email)
    }


@router.post("/register/verify-otp", response_model=UserOut)
def register_verify_otp(
    payload: VerifyRegisterOTPRequest,
    db: Session = Depends(get_db)
):
    # verify otp
    result = verify_otp(payload.email, payload.otp)
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["reason"]
        )

    # get stored registration data
    reg_data = get_registration_data(payload.email)
    if not reg_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration data expired. Please start over."
        )

    # check email not taken during OTP wait time
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # create user
    user = User(
        email=reg_data["email"],
        password_hash=hash_password(reg_data["password"]),
        name=reg_data["name"],
        gender=reg_data["gender"],
        age=reg_data["age"],
        height_cm=reg_data["height_cm"],
        initial_weight=reg_data.get("initial_weight")
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    clear_registration_data(payload.email)
    return user


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}