from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    Role,
    UserContext,
    create_access_token,
    get_current_user,
    verify_password,
)
from app.core.logging import get_logger
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.config import get_settings

router = APIRouter()
logger = get_logger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    settings = get_settings()

    try:
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.exception("login_db_error", email=data.email)
        raise HTTPException(
            status_code=503,
            detail="Authentication service temporarily unavailable",
        ) from exc

    # Dev fallback when the users table hasn't been seeded yet
    if not user and data.email == "admin@sentinelai.io" and settings.app_env == "development":
        logger.warning("demo_fallback_login", email=data.email)
        token = create_access_token("demo-admin", settings.default_tenant_id, Role.ADMIN)
        return TokenResponse(access_token=token, expires_in=1800)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id, user.tenant_id, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user.user_id))
    db_user = result.scalar_one_or_none()

    if db_user:
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            tenant_id=db_user.tenant_id,
            role=db_user.role,
        )

    return UserResponse(
        id=user.user_id,
        email=user.email,
        full_name="Demo User",
        tenant_id=user.tenant_id,
        role=user.role,
    )
