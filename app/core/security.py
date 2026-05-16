import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    email: str
    token_type: str
    jti: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_claims(user: User, token_type: str, expires_delta: timedelta) -> dict:
    now = _utcnow()
    expire = now + expires_delta
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": uuid.uuid4().hex,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return claims


def _encode_token(claims: dict) -> str:
    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def _decode_options() -> dict:
    options = {
        "verify_exp": True,
        "verify_iat": True,
        "require_exp": True,
        "require_iat": True,
        "require_sub": True,
    }
    return options


def create_access_token(user: User) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    claims = _build_claims(user, TOKEN_TYPE_ACCESS, expires_delta)
    token = _encode_token(claims)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user: User) -> str:
    expires_delta = timedelta(days=settings.refresh_token_expire_days)
    claims = _build_claims(user, TOKEN_TYPE_REFRESH, expires_delta)
    return _encode_token(claims)


def decode_token(token: str, *, expected_type: str) -> TokenPayload | None:
    try:
        decode_kwargs: dict = {
            "key": settings.secret_key,
            "algorithms": [settings.algorithm],
            "options": _decode_options(),
        }
        if settings.jwt_issuer:
            decode_kwargs["issuer"] = settings.jwt_issuer
        if settings.jwt_audience:
            decode_kwargs["audience"] = settings.jwt_audience

        payload = jwt.decode(token, **decode_kwargs)

        token_type = payload.get("type")
        if token_type != expected_type:
            return None

        sub = payload.get("sub")
        email = payload.get("email")
        jti = payload.get("jti")
        if sub is None or email is None or jti is None:
            return None

        return TokenPayload(
            user_id=int(sub),
            email=str(email).lower(),
            token_type=token_type,
            jti=jti,
        )
    except (JWTError, ValueError, TypeError):
        return None


def build_token_response(user: User) -> dict:
    access_token, expires_in = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }
