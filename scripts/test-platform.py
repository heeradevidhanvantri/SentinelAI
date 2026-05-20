#!/usr/bin/env python3
"""End-to-end platform validation for SentinelAI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow importing shared utilities when run directly
sys.path.insert(0, str(Path(__file__).parent))

from _platform_utils import (  # noqa: E402
    API_URL,
    FRONTEND_URL,
    KAFKA_BOOTSTRAP,
    PROMETHEUS_URL,
    REDIS_URL,
    CheckReport,
    auth_headers,
    c,
    get_client,
    login,
    ok,
    fail,
    info,
    Color,
)

DATABASE_URL = __import__("_platform_utils").DATABASE_URL


def check_redis() -> str:
    import redis

    client = redis.from_url(REDIS_URL)
    pong = client.ping()
    if not pong:
        raise RuntimeError("Redis ping failed")
    return f"ping OK ({REDIS_URL})"


def check_postgres() -> str:
    url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    try:
        import psycopg2
    except ImportError:
        # Fallback: verify via API DB-dependent endpoint
        with get_client() as client:
            token = login(client)
            resp = client.get(f"{API_URL}/api/v1/incidents", headers=auth_headers(token))
            if resp.status_code not in (200, 401, 403):
                raise RuntimeError(f"API/DB check failed: HTTP {resp.status_code}")
        return "connectivity verified via API (install psycopg2 for direct check)"

    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.close()
    conn.close()
    return "SELECT 1 OK"


def check_kafka() -> str:
    from kafka import KafkaAdminClient

    admin = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        request_timeout_ms=10000,
        api_version_auto_timeout_ms=10000,
    )
    cluster = admin.describe_cluster()
    admin.close()
    brokers = len(cluster.get("brokers", []))
    return f"{brokers} broker(s) reachable at {KAFKA_BOOTSTRAP}"


def validate_api_flow(client, token: str) -> str:
    headers = auth_headers(token)
    incident_payload = {
        "title": "Platform validation incident",
        "description": "Automated E2E test incident",
        "service": "validation-service",
        "severity": "high",
    }
    create_resp = client.post(f"{API_URL}/api/v1/incidents", json=incident_payload, headers=headers)
    create_resp.raise_for_status()
    incident = create_resp.json()
    incident_id = incident["id"]

    list_resp = client.get(f"{API_URL}/api/v1/incidents", headers=headers)
    list_resp.raise_for_status()
    if list_resp.json()["total"] < 1:
        raise RuntimeError("Incident list empty after create")

    trigger_resp = client.post(
        f"{API_URL}/api/v1/incidents/trigger",
        json={
            "incident_id": incident_id,
            "title": incident_payload["title"],
            "description": incident_payload["description"],
            "service": incident_payload["service"],
            "severity": "high",
        },
        headers=headers,
        timeout=180,
    )
    trigger_resp.raise_for_status()

    agents_resp = client.get(f"{API_URL}/api/v1/agents/activity", headers=headers)
    agents_resp.raise_for_status()

    timeline_resp = client.get(
        f"{API_URL}/api/v1/agents/{incident_id}/timeline", headers=headers
    )
    timeline_resp.raise_for_status()

    eval_resp = client.post(
        f"{API_URL}/api/v1/evaluation/score",
        json={
            "predicted_root_cause": "Connection pool exhaustion",
            "actual_root_cause": "Connection pool exhaustion",
            "execution_success": True,
            "resolution_time_seconds": 120,
            "reasoning_traces": ["monitoring", "investigation", "decision"],
        },
        headers=headers,
    )
    eval_resp.raise_for_status()
    score = eval_resp.json()

    remediation_resp = client.get(f"{API_URL}/api/v1/remediation/pending", headers=headers)
    remediation_resp.raise_for_status()

    return (
        f"incident={incident_id}, traces={len(timeline_resp.json().get('timeline', []))}, "
        f"eval_score={score.get('overall_score', 'n/a')}"
    )


def validate_frontend(client) -> str:
    routes = ["/", "/incidents", "/analytics", "/approvals", "/agents"]
    for route in routes:
        resp = client.get(f"{FRONTEND_URL}{route}")
        if resp.status_code != 200:
            raise RuntimeError(f"Frontend {route} returned HTTP {resp.status_code}")
    health = client.get(f"{API_URL}/health")
    health.raise_for_status()
    if health.json().get("status") != "ok":
        raise RuntimeError("API health mismatch for frontend integration")
    return f"{len(routes)} routes OK, API env reachable"


def main() -> int:
    print(c("\nSentinelAI Platform Validation", Color.BOLD))
    print(info(f"API: {API_URL} | Frontend: {FRONTEND_URL}\n"))

    report = CheckReport()

    print(c("Infrastructure", Color.BOLD))
    report.run("API reachable", lambda: (
        get_client().get(f"{API_URL}/health").raise_for_status() or f"{API_URL}/health OK"
    ))
    report.run("Frontend reachable", lambda: (
        get_client().get(FRONTEND_URL).raise_for_status() or f"{FRONTEND_URL} OK"
    ))
    report.run("Redis reachable", check_redis)
    report.run("Postgres reachable", check_postgres)
    report.run("Kafka reachable", check_kafka)
    report.run("Prometheus reachable", lambda: (
        get_client().get(f"{PROMETHEUS_URL}/-/healthy").raise_for_status()
        or f"{PROMETHEUS_URL} OK"
    ))

    print(c("\nHealth Checks", Color.BOLD))
    report.run("GET /health", lambda: (
        "status=ok" if get_client().get(f"{API_URL}/health").json().get("status") == "ok"
        else (_ for _ in ()).throw(RuntimeError("Expected status=ok"))
    ))

    print(c("\nAPI Validation", Color.BOLD))
    def api_flow():
        with get_client(timeout=180) as client:
            token = login(client)
            return validate_api_flow(client, token)
    report.run("Incident & agent API flow", api_flow)

    print(c("\nFrontend Validation", Color.BOLD))
    report.run("Dashboard & routes", lambda: validate_frontend(get_client()))

    return report.summary()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(fail("\nValidation interrupted"))
        sys.exit(130)
