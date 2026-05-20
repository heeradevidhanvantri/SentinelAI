"""Auth API schemas."""

from pydantic import BaseModel, EmailStr
from app.core.auth import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    tenant_id: str
    role: Role

    model_config = {"from_attributes": True}
