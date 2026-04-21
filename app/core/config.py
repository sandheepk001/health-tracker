from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SES_SMTP_HOST: str = ""
    SES_SMTP_PORT: int = 587
    SES_SMTP_USER: str = ""
    SES_SMTP_PASS: str = ""
    SES_SENDER_EMAIL: str = ""

    class Config:
        env_file = ".env"

settings = Settings()