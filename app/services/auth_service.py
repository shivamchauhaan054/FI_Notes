import logging
import smtplib

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.services.email_service import send_otp_email, smtp_configured
from app.services.otp import generate_otp, hash_otp, otp_expiry

logger = logging.getLogger(__name__)


def issue_otp(user: User, db: Session, purpose: str = "verify your account") -> str:
    otp = generate_otp()
    user.otp_hash = hash_otp(otp)
    user.otp_expires_at = otp_expiry()
    db.commit()

    if smtp_configured():
        try:
            email_sent = send_otp_email(user.email, otp, purpose=purpose)
            if not email_sent:
                # Network blocked by host (e.g. Railway firewall) — OTP shown on screen
                logger.warning(
                    "SMTP blocked by host network for %s. OTP returned to client.",
                    user.email,
                )
        except smtplib.SMTPAuthenticationError:
            # Wrong credentials — surface this clearly, don't silently swallow
            raise HTTPException(
                status_code=500,
                detail="Email server authentication failed. Check SMTP_USER and SMTP_PASSWORD.",
            )
        except Exception as exc:
            # All other errors: log but don't crash registration
            logger.error("SMTP send failed for %s: %s — falling back to on-screen OTP", user.email, exc)
    else:
        logger.warning(
            "SMTP not configured. OTP for %s: %s (set SMTP_* env vars to send real emails)",
            user.email,
            otp,
        )

    return otp


def create_email_user(db: Session, email: str, password: str, full_name: str | None = None) -> User:
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        full_name=full_name,
        auth_provider="email",
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def upsert_google_user(
    db: Session,
    *,
    email: str,
    google_id: str,
    full_name: str | None,
) -> User:
    email = email.lower()
    user = db.query(User).filter(User.email == email).first()

    if user:
        user.google_id = google_id
        user.is_verified = True
        user.auth_provider = "google"
        if full_name and not user.full_name:
            user.full_name = full_name
        user.otp_hash = None
        user.otp_expires_at = None
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=email,
        google_id=google_id,
        full_name=full_name,
        auth_provider="google",
        is_verified=True,
        hashed_password=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
