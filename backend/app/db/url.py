"""PostgreSQL DATABASE_URL normalization for async SQLAlchemy + asyncpg."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.core.logging import get_logger

logger = get_logger(__name__)

# Query parameters not supported by asyncpg/SQLAlchemy asyncpg dialect
ASYNCPG_UNSUPPORTED_QUERY_PARAMS = frozenset({"sslmode", "channel_binding"})

# sslmode values that imply TLS should be enabled via connect_args
_SSL_MODES_REQUIRING_TLS = frozenset({"require", "verify-ca", "verify-full", "prefer"})


@dataclass(frozen=True)
class DatabaseDriverInfo:
    original_scheme: str
    normalized_scheme: str
    detected_dialect: str
    driver_type: str
    async_mode: bool
    normalization_applied: bool
    stripped_params: tuple[str, ...]
    ssl_enabled: bool


def _extract_scheme(url: str) -> str:
    if "://" not in url:
        return "invalid"
    return url.split("://", 1)[0]


def normalize_database_url_with_connect_args(url: str) -> tuple[str, dict]:
    """
    Normalize a PostgreSQL URL for SQLAlchemy async engine with asyncpg.

    - postgres:// → postgresql+asyncpg://
    - postgresql:// → postgresql+asyncpg://
    - strips sslmode / channel_binding (enables ssl via connect_args when needed)
    - preserves other query parameters
    """
    if not url or "://" not in url:
        return url, {}

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    # Normalize scheme / driver (only once)
    if scheme == "postgres":
        scheme = "postgresql"

    if scheme == "postgresql" or scheme.startswith("postgresql+"):
        if "+asyncpg" not in scheme and "+psycopg" not in scheme:
            scheme = "postgresql+asyncpg"

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    connect_args: dict = {}
    stripped: list[str] = []
    filtered_pairs: list[tuple[str, str]] = []

    for key, value in query_pairs:
        key_lower = key.lower()
        if key_lower == "sslmode":
            if value in _SSL_MODES_REQUIRING_TLS:
                connect_args["ssl"] = True
            stripped.append(key)
            continue
        if key_lower in ASYNCPG_UNSUPPORTED_QUERY_PARAMS:
            stripped.append(key)
            continue
        filtered_pairs.append((key, value))

    normalized = urlunparse(
        (
            scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(filtered_pairs),
            parsed.fragment,
        )
    )
    return normalized, connect_args


def normalize_database_url(url: str) -> str:
    """Return asyncpg-compatible SQLAlchemy URL without connect_args."""
    normalized, _ = normalize_database_url_with_connect_args(url)
    return normalized


def validate_database_driver(url: str) -> DatabaseDriverInfo:
    """Inspect URL normalization and async driver compatibility."""
    original_scheme = _extract_scheme(url)
    normalized, connect_args = normalize_database_url_with_connect_args(url)
    normalized_scheme = _extract_scheme(normalized)

    parsed = urlparse(url)
    query_keys = {k.lower() for k, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    stripped = tuple(
        k for k in query_keys if k in ASYNCPG_UNSUPPORTED_QUERY_PARAMS or k == "sslmode"
    )

    dialect = "postgresql" if "postgresql" in normalized_scheme else normalized_scheme.split("+")[0]
    driver_type = "asyncpg" if "+asyncpg" in normalized_scheme else "unknown"

    return DatabaseDriverInfo(
        original_scheme=original_scheme,
        normalized_scheme=normalized_scheme,
        detected_dialect=dialect,
        driver_type=driver_type,
        async_mode=driver_type == "asyncpg",
        normalization_applied=url != normalized,
        stripped_params=stripped,
        ssl_enabled=bool(connect_args.get("ssl")),
    )


def log_database_config(url: str) -> DatabaseDriverInfo:
    """Log safe database configuration diagnostics (no credentials)."""
    info = validate_database_driver(url)
    logger.info(
        "database_url_configured",
        original_scheme=info.original_scheme,
        normalized_scheme=info.normalized_scheme,
        detected_dialect=info.detected_dialect,
        driver_type=info.driver_type,
        async_mode=info.async_mode,
        normalization_applied=info.normalization_applied,
        stripped_params=list(info.stripped_params),
        ssl_enabled=info.ssl_enabled,
    )
    return info
