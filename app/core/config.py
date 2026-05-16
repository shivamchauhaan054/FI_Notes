import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    @staticmethod
    def _get_env(key: str, default: str = "") -> str:
        val = os.getenv(key, default)
        return val.strip() if val else default

    @property
    def database_url(self) -> str: return self._get_env("DATABASE_URL", "sqlite:///./notes.db")
    
    @property
    def secret_key(self) -> str: return self._get_env("SECRET_KEY", "change-me-in-production")
    
    @property
    def algorithm(self) -> str: return self._get_env("ALGORITHM", "HS256")
    
    @property
    def access_token_expire_minutes(self) -> int: 
        return int(self._get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
    @property
    def refresh_token_expire_days(self) -> int:
        return int(self._get_env("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
    @property
    def jwt_issuer(self) -> str: return self._get_env("JWT_ISSUER", "fi-notes-api")
    
    @property
    def jwt_audience(self) -> str: return self._get_env("JWT_AUDIENCE", "fi-notes-app")
    
    @property
    def otp_expire_minutes(self) -> int: return int(self._get_env("OTP_EXPIRE_MINUTES", "10"))

    @property
    def app_base_url(self) -> str: return self._get_env("APP_BASE_URL", "http://127.0.0.1:8000")
    
    @property
    def frontend_url(self) -> str: return self._get_env("FRONTEND_URL", "http://127.0.0.1:8000")

    @property
    def smtp_host(self) -> str: return self._get_env("SMTP_HOST", "")
    
    @property
    def smtp_port(self) -> int: return int(self._get_env("SMTP_PORT", "587"))
    
    @property
    def smtp_user(self) -> str: return self._get_env("SMTP_USER", "")
    
    @property
    def smtp_password(self) -> str: return self._get_env("SMTP_PASSWORD", "")
    
    @property
    def smtp_from(self) -> str: return self._get_env("SMTP_FROM", "")
    
    @property
    def smtp_use_tls(self) -> bool: return _bool(os.getenv("SMTP_USE_TLS"), True)

    @property
    def google_client_id(self) -> str: return self._get_env("GOOGLE_CLIENT_ID", "")
    
    @property
    def google_client_secret(self) -> str: return self._get_env("GOOGLE_CLIENT_SECRET", "")
    
    @property
    def google_redirect_uri(self) -> str:
        return self._get_env("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback")

    @property
    def dev_show_otp(self) -> bool: return _bool(os.getenv("DEV_SHOW_OTP"), False)


settings = Settings()
