from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendOtpRequest(BaseModel):
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str
    email: EmailStr
    requires_verification: bool = True
    otp: str | None = None
    smtp_configured: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class CurrentUserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    auth_provider: str
    is_verified: bool

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
    otp: str | None = None
    smtp_configured: bool = False


class AuthStatusResponse(BaseModel):
    google_oauth_enabled: bool
    smtp_configured: bool
    google_setup_hint: str | None = None
    smtp_setup_hint: str | None = None
