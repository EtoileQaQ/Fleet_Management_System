from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: int | None = None
    role: str | None = None
    exp: int | None = None
    type: str = "access"  # "access" or "refresh"


class RefreshToken(BaseModel):
    """Refresh token request schema."""
    refresh_token: str



