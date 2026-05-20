from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, verify_password, UserContext, get_current_user, Role
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.config import get_settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Demo login for development
    if not user and data.email == "admin@sentinelai.io":
        token = create_access_token("demo-admin", get_settings().default_tenant_id, Role.ADMIN)
        return TokenResponse(access_token=token, expires_in=1800)

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id, user.tenant_id, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=get_settings().jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserContext = Depends(get_current_user)):
    return UserResponse(
        id=user.user_id,
        email=user.email,
        full_name="Demo User",
        tenant_id=user.tenant_id,
        role=user.role,
    )
