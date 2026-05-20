#!/usr/bin/env python3
"""Production readiness check for SentinelAI deployments."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _platform_utils import (  # noqa: E402
    API_URL,
    FRONTEND_URL,
    KAFKA_BOOTSTRAP,
    PROMETHEUS_URL,
    REDIS_URL,
    CheckReport,
    CheckResult,
    c,
    get_client,
    login,
    Color,
)

REQUIRED_ENV_VARS = [
    ("SECRET_KEY", "Application secret key"),
    ("JWT_SECRET_KEY", "JWT signing key"),
    ("DATABASE_URL", "PostgreSQL connection string"),
    ("REDIS_URL", "Redis connection URL"),
    ("CELERY_BROKER_URL", "Celery broker URL"),
    ("CELERY_RESULT_BACKEND", "Celery result backend URL"),
    ("KAFKA_BOOTSTRAP_SERVERS", "Kafka bootstrap servers"),
]

OPTIONAL_ENV_VARS = [
    ("OPENAI_API_KEY", "OpenAI API for LLM agents"),
    ("PINECONE_API_KEY", "Pinecone for RAG runbooks"),
    ("PINECONE_INDEX", "Pinecone index name"),
    ("OTEL_EXPORTER_OTLP_ENDPOINT", "OpenTelemetry collector"),
    ("PROMETHEUS_URL", "Prometheus server URL"),
]


def check_env_vars(report: CheckReport) -> None:
    print(c("Environment Variables", Color.BOLD))
    for var, desc in REQUIRED_ENV_VARS:
        value = os.getenv(var, "")
        def _check(v=value, d=desc, name=var):
            if not v or v.startswith("change-me"):
                raise RuntimeError(f"{name} missing or default ({d})")
            return f"{name} configured"
        report.run(f"ENV {var}", _check)

    print(c("\nOptional Integrations", Color.BOLD))
    for var, desc in OPTIONAL_ENV_VARS:
        value = os.getenv(var, "")
        if value:
            report.add(CheckResult(f"ENV {var}", True, "configured"))
            print(f"  ✓ {var}: configured")
        else:
            report.add(CheckResult(f"ENV {var}", True, "not set (optional)"))
            print(f"  · {var}: not set — {desc}")


def check_connectivity(report: CheckReport) -> None:
    print(c("\nConnectivity", Color.BOLD))

    report.run("Redis", lambda: __import__("redis").from_url(REDIS_URL).ping() or "ping OK")

    report.run("API health", lambda: (
        "ok" if get_client().get(f"{API_URL}/health").json().get("status") == "ok"
        else (_ for _ in ()).throw(RuntimeError("unhealthy"))
    ))

    report.run("Frontend", lambda: (
        get_client().get(FRONTEND_URL).raise_for_status() or f"{FRONTEND_URL} OK"
    ))

    report.run("Prometheus", lambda: (
        get_client(timeout=10).get(f"{PROMETHEUS_URL}/-/healthy").raise_for_status()
        or "healthy"
    ))

    def kafka_check():
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP, request_timeout_ms=10000)
        brokers = len(admin.describe_cluster().get("brokers", []))
        admin.close()
        return f"{brokers} broker(s)"

    report.run("Kafka", kafka_check)

    def db_check():
        with get_client() as client:
            token = login(client)
            resp = client.get(
                f"{API_URL}/api/v1/incidents",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
        return "API/DB round-trip OK"

    report.run("Database (via API)", db_check)

    def openai_check():
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            return "skipped (no key — mock LLM mode)"
        import httpx
        resp = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if resp.status_code == 401:
            raise RuntimeError("Invalid OpenAI API key")
        return "API key accepted" if resp.status_code == 200 else f"HTTP {resp.status_code}"

    report.run("OpenAI API", openai_check)

    def pinecone_check():
        key = os.getenv("PINECONE_API_KEY", "")
        if not key:
            return "skipped (no key — mock RAG mode)"
        index = os.getenv("PINECONE_INDEX", "sentinelai-runbooks")
        return f"key configured, index={index}"

    report.run("Pinecone", pinecone_check)


def main() -> int:
    print(c("\nSentinelAI Production Readiness Check", Color.BOLD))
    print(f"  API:       {API_URL}")
    print(f"  Frontend:  {FRONTEND_URL}")
    print(f"  Redis:     {REDIS_URL}")
    print(f"  Kafka:     {KAFKA_BOOTSTRAP}\n")

    report = CheckReport()
    check_env_vars(report)
    check_connectivity(report)
    return report.summary()


if __name__ == "__main__":
    sys.exit(main())
