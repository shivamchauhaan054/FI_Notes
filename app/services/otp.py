import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    payload = f"{otp}:{settings.secret_key}".encode()
    return hashlib.sha256(payload).hexdigest()


def verify_otp(otp: str, otp_hash: str | None) -> bool:
    if not otp_hash:
        return False
    return secrets.compare_digest(hash_otp(otp), otp_hash)


def otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)


def is_otp_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    expires = expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires
