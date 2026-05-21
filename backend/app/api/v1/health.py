from fastapi import APIRouter, Response

from app import __version__
from app.core.auth import hash_password, validate_jwt_config, verify_password
from app.core.observability import metrics_response
from app.db.init_db import check_database_connectivity, users_table_exists
from app.db.url import validate_database_driver
from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": __version__, "service": "sentinelai-api"}


@router.get("/health/auth")
async def auth_health_check():
    """Structured auth subsystem diagnostics for production debugging."""
    settings = get_settings()
    jwt_warnings = validate_jwt_config()

    db_connected = await check_database_connectivity()
    table_exists = await users_table_exists() if db_connected else False

    bcrypt_ok = False
    bcrypt_error: str | None = None
    try:
        sample_hash = hash_password("__health_check__")
        bcrypt_ok = verify_password("__health_check__", sample_hash)
    except Exception as exc:
        bcrypt_error = str(exc)

    jwt_configured = len(jwt_warnings) == 0
    driver_info = validate_database_driver(settings.database_url)

    checks = {
        "database_connected": db_connected,
        "users_table_exists": table_exists,
        "jwt_configured": jwt_configured,
        "bcrypt_working": bcrypt_ok,
        "asyncpg_driver": driver_info.async_mode,
    }
    all_ok = all(checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
        "jwt": {
            "algorithm": settings.jwt_algorithm,
            "access_token_expire_minutes": settings.jwt_access_token_expire_minutes,
            "warnings": jwt_warnings,
        },
        "database": {
            "driver": driver_info.driver_type,
            "url_scheme": driver_info.normalized_scheme,
            "original_scheme": driver_info.original_scheme,
            "async_mode": driver_info.async_mode,
            "normalization_applied": driver_info.normalization_applied,
            "stripped_params": list(driver_info.stripped_params),
            "ssl_enabled": driver_info.ssl_enabled,
        },
        "bcrypt_error": bcrypt_error,
    }


@router.get("/metrics")
async def prometheus_metrics():
    content, content_type = metrics_response()
    return Response(content=content, media_type=content_type)
