from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.oauth import oauth
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    build_token_response,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthStatusResponse,
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResendOtpRequest,
    VerifyOtpRequest,
)
from app.services.auth_service import create_email_user, issue_otp, upsert_google_user
from app.services.email_service import smtp_configured
from app.services.otp import is_otp_expired, verify_otp

router = APIRouter(tags=["auth"])


def _login_response(user: User) -> LoginResponse:
    return LoginResponse(**build_token_response(user))


@router.get("/auth/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the current authenticated user's profile information.
    """
    return current_user


@router.post("/auth/refresh", response_model=LoginResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh an expired access token using a valid refresh token.
    """
    token_data = decode_token(payload.refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None or user.email != token_data.email or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return _login_response(user)


def _google_enabled() -> bool:
    return bool(
        settings.google_client_id
        and settings.google_client_secret
        and "your-google" not in settings.google_client_id.lower()
    )


@router.get("/auth/status", response_model=AuthStatusResponse)
def auth_status():
    """
    Check the configuration status of external services (Google OAuth, SMTP).
    """
    google_on = _google_enabled()
    smtp_on = smtp_configured()
    return AuthStatusResponse(
        google_oauth_enabled=google_on,
        smtp_configured=smtp_on,
        google_setup_hint=None
        if google_on
        else "Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file (see README).",
        smtp_setup_hint=None
        if smtp_on
        else "Add SMTP_* settings to .env to receive codes by email. Until then, the code is shown on screen.",
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with an email and password. 
    Initiates the OTP verification flow.
    """
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        if existing.auth_provider == "google":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is registered with Google. Sign in with Google.",
            )
        existing.hashed_password = get_password_hash(payload.password)
        if payload.full_name:
            existing.full_name = payload.full_name
        user = existing
    else:
        user = create_email_user(db, email, payload.password, payload.full_name)

    otp = issue_otp(user, db, purpose="verify your account")
    db.refresh(user)

    smtp_on = smtp_configured()
    message = (
        "Verification code sent to your email. Enter it below to activate your account."
        if smtp_on
        else "Email is not configured on the server. Use the verification code shown below."
    )
    return RegisterResponse(
        message=message,
        email=email,
        smtp_configured=smtp_on,
        otp=otp if (not smtp_on or settings.dev_show_otp) else None,
    )


@router.post("/verify-otp", response_model=LoginResponse)
def verify_otp_endpoint(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Verify a user's account using the 6-digit OTP code.
    """
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found. Please register first.",
        )

    if user.is_verified:
        return _login_response(user)

    if is_otp_expired(user.otp_expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Request a new code.",
        )

    if not verify_otp(payload.otp, user.otp_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    user.is_verified = True
    user.otp_hash = None
    user.otp_expires_at = None
    db.commit()

    return _login_response(user)


@router.post("/resend-otp", response_model=MessageResponse)
def resend_otp(payload: ResendOtpRequest, db: Session = Depends(get_db)):
    """
    Request a new OTP code if the previous one expired or was not received.
    """
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    if user.auth_provider == "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google sign-in",
        )

    otp = issue_otp(user, db, purpose="verify your account")
    smtp_on = smtp_configured()
    message = (
        "A new verification code has been sent to your email"
        if smtp_on
        else "Email not configured — use the verification code shown below"
    )
    return MessageResponse(
        message=message,
        smtp_configured=smtp_on,
        otp=otp if (not smtp_on or settings.dev_show_otp) else None,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user with email and password. 
    Returns JWT access and refresh tokens.
    """
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()

    if user is None or not user.hashed_password:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid email or password"},
        )

    if not verify_password(payload.password, user.hashed_password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid email or password"},
        )

    if not user.is_verified:
        otp = issue_otp(user, db, purpose="complete your sign in")
        smtp_on = smtp_configured()
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": (
                    "Email not verified. A new verification code has been sent to your email."
                    if smtp_on
                    else "Email not verified. Use the verification code shown below."
                ),
                "requires_verification": True,
                "email": email,
                "smtp_configured": smtp_on,
                "otp": otp if (not smtp_on or settings.dev_show_otp) else None,
            },
        )

    return _login_response(user)


@router.get("/auth/google")
async def google_login(request: Request):
    """
    Initiate the Google OAuth 2.0 authorization flow.
    """
    if not _google_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your .env file.",
        )
    return await oauth.google.authorize_redirect(
        request, settings.google_redirect_uri
    )


@router.get("/auth/google/callback", include_in_schema=False)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Callback handler for Google OAuth. 
    Handles user creation/login and redirects to frontend with tokens.
    """
    if not _google_enabled():
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth_error=google_not_configured"
        )

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth_error=google_auth_failed"
        )

    user_info = token.get("userinfo")
    if not user_info:
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth_error=missing_user_info"
        )

    email = user_info.get("email")
    google_id = user_info.get("sub")
    if not email or not google_id:
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth_error=invalid_google_profile"
        )

    user = upsert_google_user(
        db,
        email=email,
        google_id=google_id,
        full_name=user_info.get("name"),
    )
    tokens = build_token_response(user)
    return RedirectResponse(
        url=(
            f"{settings.frontend_url}/?"
            f"token={tokens['access_token']}"
            f"&refresh_token={tokens['refresh_token']}"
            f"&email={user.email}"
        )
    )
