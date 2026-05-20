"""JWT authentication and RBAC."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Optional, Union

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


class Role(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    role: Role
    exp: Optional[datetime] = None


class UserContext(BaseModel):
    user_id: str
    email: str
    tenant_id: str
    role: Role


def role_to_str(role: Union[Role, str]) -> str:
    return role.value if isinstance(role, Role) else str(role)


def validate_jwt_config() -> list[str]:
    """Return list of JWT configuration warnings (empty if OK)."""
    settings = get_settings()
    warnings: list[str] = []
    if not settings.jwt_secret_key or settings.jwt_secret_key.startswith("change-me"):
        warnings.append("JWT_SECRET_KEY is missing or using default placeholder")
    if not settings.jwt_algorithm:
        warnings.append("JWT_ALGORITHM is not configured")
    if settings.jwt_access_token_expire_minutes <= 0:
        warnings.append("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
    return warnings


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: Optional[str]) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError, AttributeError) as exc:
        logger.warning("password_verification_failed", error=str(exc))
        return False


def create_access_token(user_id: str, tenant_id: str, role: Union[Role, str]) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role_to_str(role),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    try:
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    except Exception as exc:
        logger.exception("jwt_token_creation_failed", user_id=user_id, error=str(exc))
        raise RuntimeError("Failed to create access token") from exc


def decode_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return TokenPayload(
            sub=payload["sub"],
            tenant_id=payload.get("tenant_id", settings.default_tenant_id),
            role=Role(payload.get("role", Role.VIEWER.value)),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> UserContext:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    payload = decode_token(credentials.credentials)
    return UserContext(
        user_id=payload.sub,
        email=f"{payload.sub}@sentinelai.local",
        tenant_id=payload.tenant_id,
        role=payload.role,
    )


def require_role(*roles: Role):
    async def checker(user: Annotated[UserContext, Depends(get_current_user)]) -> UserContext:
        if user.role not in roles and user.role != Role.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in roles]}",
            )
        return user

    return checker
