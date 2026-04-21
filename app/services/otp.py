import random
import string
import json
from app.services.redis_client import redis_client

OTP_EXPIRY_SECONDS = 600
OTP_MAX_ATTEMPTS = 5

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email: str, otp: str):
    key = f"otp:{email}"
    attempts_key = f"otp_attempts:{email}"
    redis_client.setex(key, OTP_EXPIRY_SECONDS, otp)
    redis_client.setex(attempts_key, OTP_EXPIRY_SECONDS, 0)

def store_registration_otp(email: str, otp: str, registration_data: dict):
    key = f"otp:{email}"
    reg_key = f"reg_data:{email}"
    attempts_key = f"otp_attempts:{email}"
    redis_client.setex(key, OTP_EXPIRY_SECONDS, otp)
    redis_client.setex(reg_key, OTP_EXPIRY_SECONDS, json.dumps(registration_data))
    redis_client.setex(attempts_key, OTP_EXPIRY_SECONDS, 0)

def get_registration_data(email: str) -> dict | None:
    reg_key = f"reg_data:{email}"
    data = redis_client.get(reg_key)
    return json.loads(data) if data else None

def clear_registration_data(email: str):
    redis_client.delete(f"reg_data:{email}")

def verify_otp(email: str, otp: str) -> dict:
    key = f"otp:{email}"
    attempts_key = f"otp_attempts:{email}"
    stored_otp = redis_client.get(key)

    if not stored_otp:
        return {"valid": False, "reason": "OTP expired or not found"}

    attempts = int(redis_client.get(attempts_key) or 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        redis_client.delete(key)
        redis_client.delete(attempts_key)
        return {"valid": False, "reason": "Too many attempts. Request a new OTP."}

    if stored_otp != otp:
        redis_client.incr(attempts_key)
        remaining = OTP_MAX_ATTEMPTS - attempts - 1
        return {"valid": False, "reason": f"Invalid OTP. {remaining} attempts remaining."}

    redis_client.delete(key)
    redis_client.delete(attempts_key)
    return {"valid": True}

def delete_otp(email: str):
    redis_client.delete(f"otp:{email}")
    redis_client.delete(f"otp_attempts:{email}")

def get_otp_ttl(email: str) -> int:
    return redis_client.ttl(f"otp:{email}")