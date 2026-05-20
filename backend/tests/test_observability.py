"""Observability validation — Prometheus metrics and OpenTelemetry."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
API_URL = os.getenv("SENTINEL_API_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/metrics")
    assert response.status_code == 200
    body = response.text
    assert "sentinelai_http_request_duration_seconds" in body


@pytest.mark.asyncio
async def test_metrics_recorded_after_request(async_client: AsyncClient):
    await async_client.get("/health")
    response = await async_client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "sentinelai_http_request_duration_seconds" in response.text


def test_prometheus_metric_definitions():
    from app.core.observability import (
        AGENT_INVOCATIONS,
        AGENT_LATENCY,
        REQUEST_LATENCY,
        TOKEN_USAGE,
        ACTIVE_INCIDENTS,
        REMEDIATION_SUCCESS,
        CIRCUIT_BREAKER_STATE,
    )

    assert REQUEST_LATENCY._name == "sentinelai_http_request_duration_seconds"
    assert AGENT_INVOCATIONS._name == "sentinelai_agent_invocations_total"
    assert AGENT_LATENCY._name == "sentinelai_agent_duration_seconds"
    assert TOKEN_USAGE._name == "sentinelai_llm_tokens_total"
    assert ACTIVE_INCIDENTS._name == "sentinelai_active_incidents"
    assert REMEDIATION_SUCCESS._name == "sentinelai_remediation_success_total"
    assert CIRCUIT_BREAKER_STATE._name == "sentinelai_circuit_breaker_open"


@pytest.mark.asyncio
async def test_agent_metrics_after_pipeline(sample_incident_input):
    from app.agents.graph import run_incident_pipeline
    from app.core.observability import AGENT_INVOCATIONS

    before = AGENT_INVOCATIONS._metrics.copy() if hasattr(AGENT_INVOCATIONS, "_metrics") else {}

    await run_incident_pipeline(
        incident_id="obs-001",
        tenant_id="default",
        alert_title="Observability test incident",
        alert_description="Validate agent metrics",
        service="observability-test",
        severity="medium",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/metrics")
    assert "sentinelai_agent_invocations_total" in resp.text


def test_setup_telemetry_does_not_crash():
    from fastapi import FastAPI
    from app.core.observability import setup_telemetry

    test_app = FastAPI()
    setup_telemetry(test_app)  # Should swallow OTEL connection errors in dev


@pytest.mark.integration
def test_prometheus_server_reachable():
    import httpx

    try:
        resp = httpx.get(f"{PROMETHEUS_URL}/-/healthy", timeout=10)
    except Exception:
        pytest.skip("Prometheus not available")
    assert resp.status_code == 200


@pytest.mark.integration
def test_api_latency_metrics_via_live_api():
    import httpx

    try:
        client = httpx.Client(base_url=API_URL, timeout=10)
        client.get("/health")
        resp = client.get("/api/v1/metrics")
        client.close()
    except Exception:
        pytest.skip("API not available")

    assert resp.status_code == 200
    assert "sentinelai_http_request_duration_seconds" in resp.text


def test_metrics_response_content_type():
    from app.core.observability import metrics_response, CONTENT_TYPE_LATEST

    body, content_type = metrics_response()
    assert content_type == CONTENT_TYPE_LATEST
    assert len(body) > 0
