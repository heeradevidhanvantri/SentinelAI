"""Database URL normalization and driver validation tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.url import (
    normalize_database_url,
    normalize_database_url_with_connect_args,
    validate_database_driver,
)
from app.main import app


@pytest.mark.parametrize(
    ("raw", "expected_prefix"),
    [
        ("postgres://user:pass@host/db", "postgresql+asyncpg://"),
        ("postgresql://user:pass@host/db", "postgresql+asyncpg://"),
        ("postgresql+asyncpg://user:pass@host/db", "postgresql+asyncpg://"),
    ],
)
def test_scheme_normalization(raw: str, expected_prefix: str):
    normalized = normalize_database_url(raw)
    assert normalized.startswith(expected_prefix)
    assert "user:pass@host/db" in normalized


def test_sslmode_stripped_and_ssl_connect_arg_enabled():
    raw = "postgresql://user:pass@neon.host/db?sslmode=require"
    normalized, connect_args = normalize_database_url_with_connect_args(raw)
    assert normalized.startswith("postgresql+asyncpg://")
    assert "sslmode" not in normalized
    assert connect_args.get("ssl") is True


def test_channel_binding_stripped():
    raw = "postgresql://user:pass@host/db?channel_binding=require&sslmode=require"
    normalized, connect_args = normalize_database_url_with_connect_args(raw)
    assert "channel_binding" not in normalized
    assert "sslmode" not in normalized
    assert connect_args.get("ssl") is True


def test_preserves_unrelated_query_params():
    raw = "postgresql://user:pass@host/db?sslmode=require&options=-c%20search_path%3Dpublic"
    normalized, _ = normalize_database_url_with_connect_args(raw)
    assert "options=" in normalized
    assert "sslmode" not in normalized


def test_already_correct_asyncpg_url_unchanged_except_params():
    raw = "postgresql+asyncpg://user:pass@host:5432/sentinelai"
    normalized = normalize_database_url(raw)
    assert normalized == raw


def test_neon_style_url():
    raw = (
        "postgres://user:pass@ep-cool-name.us-east-2.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    info = validate_database_driver(raw)
    assert info.normalized_scheme == "postgresql+asyncpg"
    assert info.async_mode is True
    assert info.normalization_applied is True
    assert "sslmode" in info.stripped_params
    assert info.ssl_enabled is True

    normalized, connect_args = normalize_database_url_with_connect_args(raw)
    assert normalized.startswith("postgresql+asyncpg://")
    assert connect_args["ssl"] is True


def test_malformed_url_returns_unchanged():
    malformed = "not-a-valid-database-url"
    normalized, connect_args = normalize_database_url_with_connect_args(malformed)
    assert normalized == malformed
    assert connect_args == {}


def test_validate_database_driver():
    info = validate_database_driver("postgresql://localhost/db")
    assert info.detected_dialect == "postgresql"
    assert info.driver_type == "asyncpg"
    assert info.async_mode is True
    assert info.normalization_applied is True
    assert info.original_scheme == "postgresql"
    assert info.normalized_scheme == "postgresql+asyncpg"


@pytest.mark.asyncio
async def test_health_endpoint_reports_normalized_driver(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@host/db?sslmode=require",
    )
    from app.config import get_settings
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/auth")

    get_settings.cache_clear()
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["asyncpg_driver"] is True
    assert data["database"]["url_scheme"] == "postgresql+asyncpg"
    assert data["database"]["driver"] == "asyncpg"
    assert data["database"]["normalization_applied"] is True
