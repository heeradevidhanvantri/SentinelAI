"""Frontend integration validation — routes, API env, backend connectivity."""

from __future__ import annotations

import os

import httpx
import pytest

API_BASE_URL = os.getenv("SENTINEL_API_URL", "http://localhost:8000")
FRONTEND_BASE_URL = os.getenv("SENTINEL_FRONTEND_URL", "http://localhost:3000")


def skip_if_unavailable(url: str, name: str, path: str = "/"):
    try:
        resp = httpx.get(f"{url}{path}", timeout=5.0)
        if resp.status_code >= 500:
            pytest.skip(f"{name} not available at {url}")
    except Exception:
        pytest.skip(f"{name} not available at {url}")

FRONTEND_ROUTES = [
    "/",
    "/incidents",
    "/analytics",
    "/approvals",
    "/agents",
    "/infrastructure",
    "/settings",
]


@pytest.mark.integration
@pytest.fixture(scope="module")
def frontend_client():
    skip_if_unavailable(FRONTEND_BASE_URL, "Frontend")
    with httpx.Client(base_url=FRONTEND_BASE_URL, timeout=15.0, follow_redirects=True) as client:
        yield client


@pytest.mark.integration
def test_frontend_dashboard_loads(frontend_client: httpx.Client):
    resp = frontend_client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


@pytest.mark.integration
@pytest.mark.parametrize("route", FRONTEND_ROUTES)
def test_frontend_routes_respond(frontend_client: httpx.Client, route: str):
    resp = frontend_client.get(route)
    assert resp.status_code == 200, f"{route} returned {resp.status_code}"


@pytest.mark.integration
def test_frontend_api_env_configuration():
    """Verify backend is reachable at the URL the frontend would use."""
    api_url = os.getenv("NEXT_PUBLIC_API_URL", API_BASE_URL)
    skip_if_unavailable(api_url, "API", "/health")

    resp = httpx.get(f"{api_url}/health", timeout=10)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


@pytest.mark.integration
def test_dashboard_backend_incidents_endpoint(auth_headers: dict):
    skip_if_unavailable(API_BASE_URL, "API", "/health")
    with httpx.Client(base_url=API_BASE_URL, timeout=15) as client:
        resp = client.get("/api/v1/incidents", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.integration
def test_analytics_evaluation_endpoint(auth_headers: dict):
    skip_if_unavailable(API_BASE_URL, "API", "/health")
    with httpx.Client(base_url=API_BASE_URL, timeout=15) as client:
        resp = client.post(
            "/api/v1/evaluation/score",
            json={
                "predicted_root_cause": "Memory leak in worker process",
                "actual_root_cause": "Memory leak in worker process",
                "execution_success": True,
                "resolution_time_seconds": 300,
                "reasoning_traces": ["monitoring", "investigation"],
            },
            headers=auth_headers,
        )
    assert resp.status_code == 200
    score = resp.json()
    assert "overall_score" in score
    assert "hallucination_score" in score


@pytest.mark.integration
def test_approvals_endpoint(auth_headers: dict):
    skip_if_unavailable(API_BASE_URL, "API", "/health")
    with httpx.Client(base_url=API_BASE_URL, timeout=15) as client:
        resp = client.get("/api/v1/remediation/pending", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.integration
def test_agent_activity_feed(auth_headers: dict):
    skip_if_unavailable(API_BASE_URL, "API", "/health")
    with httpx.Client(base_url=API_BASE_URL, timeout=15) as client:
        resp = client.get("/api/v1/agents/activity", headers=auth_headers)
    assert resp.status_code == 200
    assert "feed" in resp.json()


@pytest.mark.integration
def test_monitoring_health_endpoint(auth_headers: dict):
    skip_if_unavailable(API_BASE_URL, "API", "/health")
    with httpx.Client(base_url=API_BASE_URL, timeout=15) as client:
        resp = client.get("/api/v1/monitoring/health", headers=auth_headers)
    assert resp.status_code == 200
    health = resp.json()
    assert isinstance(health, list)
    assert len(health) > 0
