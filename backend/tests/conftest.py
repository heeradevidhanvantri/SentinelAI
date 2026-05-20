"""Pytest fixtures and shared test utilities for SentinelAI."""

from __future__ import annotations

import os
from typing import AsyncGenerator, Generator

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Service URLs for integration tests (Docker-aware)
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("SENTINEL_API_URL", "http://localhost:8000")
FRONTEND_BASE_URL = os.getenv("SENTINEL_FRONTEND_URL", "http://localhost:3000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

DEMO_EMAIL = "admin@sentinelai.io"
DEMO_PASSWORD = "demo"

# Skip integration tests when services are unavailable
INTEGRATION = pytest.mark.integration
SLOW = pytest.mark.slow


def service_available(url: str, path: str = "/") -> bool:
    try:
        resp = httpx.get(f"{url}{path}", timeout=5.0)
        return resp.status_code < 500
    except Exception:
        return False


def skip_if_unavailable(url: str, name: str, path: str = "/"):
    if not service_available(url, path):
        pytest.skip(f"{name} not available at {url}")


@pytest.fixture
def sample_incident_input():
    return {
        "incident_id": "test-001",
        "tenant_id": "default",
        "alert_title": "High error rate",
        "alert_description": "Error rate > 3%",
        "service": "payment-api",
        "severity": "high",
    }


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_api_client() -> Generator[httpx.Client, None, None]:
    skip_if_unavailable(API_BASE_URL, "API", "/health")
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def auth_token(sync_api_client: httpx.Client) -> str:
    resp = sync_api_client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
