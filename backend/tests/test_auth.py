"""Authentication flow tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import Role, create_access_token, hash_password, verify_password
from app.db.base import get_db
from app.db.init_db import DEMO_USER_EMAIL, DEMO_USER_PASSWORD
from app.main import app


def _make_user(password: str = DEMO_USER_PASSWORD):
    return SimpleNamespace(
        id="user-001",
        email=DEMO_USER_EMAIL,
        tenant_id="default",
        hashed_password=hash_password(password),
        full_name="Test Admin",
        role=Role.ADMIN,
        is_active=True,
    )


def _mock_db_session(user):
    async def override_get_db():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = user
        session.execute = AsyncMock(return_value=result)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return override_get_db


@pytest.fixture
async def auth_client():
    app.dependency_overrides[get_db] = _mock_db_session(_make_user())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client_no_user():
    app.dependency_overrides[get_db] = _mock_db_session(None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_success(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_USER_EMAIL, "password": DEMO_USER_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("token_type", "bearer") == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_USER_EMAIL, "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_missing_user(auth_client_no_user: AsyncClient):
    response = await auth_client_no_user.post(
        "/api/v1/auth/login",
        json={"email": "nobody@sentinelai.io", "password": "any"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_jwt_generation():
    token = create_access_token("user-123", "default", Role.ADMIN)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3


@pytest.mark.asyncio
async def test_jwt_generation_with_string_role():
    token = create_access_token("user-123", "default", "admin")
    assert isinstance(token, str)


def test_password_hash_and_verify():
    hashed = hash_password("sentinel123")
    assert verify_password("sentinel123", hashed)
    assert not verify_password("wrong", hashed)


def test_password_verify_invalid_hash():
    assert verify_password("sentinel123", None) is False
    assert verify_password("sentinel123", "not-a-valid-hash") is False


@pytest.mark.asyncio
async def test_auth_health_endpoint(auth_client: AsyncClient):
    response = await auth_client.get("/api/v1/health/auth")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "bcrypt_working" in data["checks"]
    assert data["checks"]["bcrypt_working"] is True


@pytest.mark.asyncio
async def test_login_returns_request_id_header(auth_client: AsyncClient):
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_USER_EMAIL, "password": DEMO_USER_PASSWORD},
        headers={"X-Request-ID": "test-correlation-123"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "test-correlation-123"
