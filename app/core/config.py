import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./notes.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    refresh_token_expire_days: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )
    jwt_issuer: str = os.getenv("JWT_ISSUER", "notes-api")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "notes-app")
    otp_expire_minutes: int = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))

    app_base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "")
    smtp_use_tls: bool = _bool(os.getenv("SMTP_USE_TLS"), True)

    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8000/auth/google/callback",
    )

    dev_show_otp: bool = _bool(os.getenv("DEV_SHOW_OTP"), False)


settings = Settings()
