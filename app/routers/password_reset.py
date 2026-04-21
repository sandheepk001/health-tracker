from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.core.security import hash_password
from app.services.otp import generate_otp, store_otp, verify_otp, get_otp_ttl
from app.services.email import send_otp_email

router = APIRouter(prefix="/auth", tags=["Password Reset"])

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

# store verified emails temporarily so reset step
# knows OTP was already verified
import redis
from app.services.redis_client import redis_client

def mark_otp_verified(email: str):
    redis_client.setex(f"otp_verified:{email}", 600, "1")

def is_otp_verified(email: str) -> bool:
    return redis_client.get(f"otp_verified:{email}") == "1"

def clear_verified(email: str):
    redis_client.delete(f"otp_verified:{email}")


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()

    # always return success to prevent email enumeration
    if not user:
        return {"detail": "If this email is registered, an OTP has been sent."}

    otp = generate_otp()
    store_otp(payload.email, otp)
    send_otp_email(payload.email, otp, user.name)

    ttl = get_otp_ttl(payload.email)
    return {
        "detail": "OTP sent successfully.",
        "expires_in": ttl
    }


@router.post("/verify-otp")
def verify_otp_route(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    result = verify_otp(payload.email, payload.otp)

    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["reason"]
        )

    # mark as verified so reset step knows
    mark_otp_verified(payload.email)
    return {"detail": "OTP verified successfully."}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # verify OTP again as final check
    if not is_otp_verified(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not verified. Please verify OTP first."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters."
        )

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    clear_verified(payload.email)
    return {"detail": "Password reset successfully."}