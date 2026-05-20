from fastapi import APIRouter, Depends, HTTPException, Request
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
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    request_id = getattr(request.state, "request_id", None)
    settings = get_settings()

    logger.info(
        "auth_login_attempt",
        email=data.email,
        request_id=request_id,
    )

    user: User | None = None
    try:
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.exception(
            "auth_login_db_error",
            email=data.email,
            request_id=request_id,
            error=str(exc),
        )
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable") from exc

    # Dev/demo fallback when users table is empty (no row found, not a DB error)
    if not user and data.email == "admin@sentinelai.io" and settings.app_env == "development":
        logger.warning(
            "auth_demo_fallback_login",
            email=data.email,
            request_id=request_id,
        )
        try:
            token = create_access_token("demo-admin", settings.default_tenant_id, Role.ADMIN)
            return TokenResponse(access_token=token, expires_in=1800)
        except Exception as exc:
            logger.exception(
                "auth_demo_token_error",
                email=data.email,
                request_id=request_id,
                error=str(exc),
            )
            raise HTTPException(status_code=500, detail="Failed to generate token") from exc

    if not user:
        logger.warning(
            "auth_login_user_not_found",
            email=data.email,
            request_id=request_id,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        logger.warning(
            "auth_login_inactive_user",
            email=data.email,
            user_id=user.id,
            request_id=request_id,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        password_valid = verify_password(data.password, user.hashed_password)
    except Exception as exc:
        logger.exception(
            "auth_login_password_error",
            email=data.email,
            user_id=user.id,
            request_id=request_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Authentication processing error") from exc

    if not password_valid:
        logger.warning(
            "auth_login_invalid_password",
            email=data.email,
            user_id=user.id,
            request_id=request_id,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        token = create_access_token(user.id, user.tenant_id, user.role)
    except Exception as exc:
        logger.exception(
            "auth_login_jwt_error",
            email=data.email,
            user_id=user.id,
            request_id=request_id,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail="Failed to generate token") from exc

    logger.info(
        "auth_login_success",
        email=data.email,
        user_id=user.id,
        request_id=request_id,
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
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
