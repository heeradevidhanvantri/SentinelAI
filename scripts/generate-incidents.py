#!/usr/bin/env python3
"""Generate synthetic incidents for SentinelAI pipeline testing and demos."""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from faker import Faker

from _platform_utils import (  # noqa: E402
    API_URL,
    auth_headers,
    c,
    fail,
    get_client,
    info,
    login,
    ok,
    Color,
)

fake = Faker()

INCIDENT_TEMPLATES = [
    {
        "title": "Kafka broker latency spike",
        "description": "P99 produce latency exceeded 500ms on broker-2; consumer lag growing.",
        "service": "kafka-broker",
        "severity": "critical",
        "metadata": {"metric": "kafka.request.latency.p99", "value_ms": 842, "threshold_ms": 500},
    },
    {
        "title": "Kubernetes pod crash loop",
        "description": "payment-api pod restarting repeatedly; CrashLoopBackOff detected.",
        "service": "payment-api",
        "severity": "critical",
        "metadata": {"namespace": "production", "pod": "payment-api-7f8d9", "restarts": 12},
    },
    {
        "title": "Redis connection saturation",
        "description": "Redis maxclients threshold reached; Celery workers timing out.",
        "service": "redis-cache",
        "severity": "high",
        "metadata": {"connected_clients": 10000, "maxclients": 10000, "rejected_connections": 340},
    },
    {
        "title": "CPU exhaustion on API nodes",
        "description": "API fleet CPU sustained above 95% for 8 minutes.",
        "service": "sentinelai-api",
        "severity": "high",
        "metadata": {"cpu_percent": 97.2, "duration_minutes": 8, "affected_nodes": 4},
    },
    {
        "title": "API timeout storm",
        "description": "Upstream dependency timeouts causing cascading 504 errors.",
        "service": "gateway-api",
        "severity": "critical",
        "metadata": {"error_rate_percent": 18.4, "timeout_ms": 30000, "affected_routes": 23},
    },
    {
        "title": "Postgres connection leak",
        "description": "Connection pool exhausted; idle-in-transaction sessions accumulating.",
        "service": "postgres-primary",
        "severity": "high",
        "metadata": {"active_connections": 498, "max_connections": 500, "idle_in_transaction": 87},
    },
]


def ingest_signals(client, token: str, incident: dict) -> None:
    headers = auth_headers(token)
    meta = incident.get("metadata", {})
    client.post(
        f"{API_URL}/api/v1/monitoring/metrics/ingest",
        json={
            "service": incident["service"],
            "metric_name": meta.get("metric", "synthetic.alert.score"),
            "value": meta.get("value_ms", meta.get("cpu_percent", meta.get("error_rate_percent", 1.0))),
            "labels": {"source": "generate-incidents", "severity": incident["severity"]},
        },
        headers=headers,
    )
    client.post(
        f"{API_URL}/api/v1/monitoring/logs/ingest",
        json={
            "service": incident["service"],
            "level": "ERROR",
            "message": incident["description"],
            "metadata": meta,
        },
        headers=headers,
    )


def generate_incident(client, token: str, template: dict, async_pipeline: bool) -> dict:
    headers = auth_headers(token)
    payload = {
        "title": template["title"],
        "description": template["description"],
        "service": template["service"],
        "severity": template["severity"],
        "metadata": template.get("metadata", {}),
    }

    ingest_signals(client, token, template)

    create_resp = client.post(f"{API_URL}/api/v1/incidents", json=payload, headers=headers)
    create_resp.raise_for_status()
    incident = create_resp.json()

    if async_pipeline:
        investigate_resp = client.post(
            f"{API_URL}/api/v1/incidents/{incident['id']}/investigate",
            headers=headers,
        )
        investigate_resp.raise_for_status()
        incident = investigate_resp.json()
        mode = "Celery async"
    else:
        trigger_resp = client.post(
            f"{API_URL}/api/v1/incidents/trigger",
            json={
                "incident_id": incident["id"],
                **payload,
            },
            headers=headers,
            timeout=180,
        )
        trigger_resp.raise_for_status()
        incident = trigger_resp.json()
        mode = "sync LangGraph"

    return {
        "id": incident["id"],
        "title": incident.get("title", payload["title"]),
        "status": incident.get("status"),
        "root_cause": incident.get("root_cause"),
        "mode": mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic SentinelAI incidents")
    parser.add_argument("-n", "--count", type=int, default=1, help="Number of incidents")
    parser.add_argument("--async", dest="async_mode", action="store_true", help="Use Celery async pipeline")
    parser.add_argument("--all-types", action="store_true", help="Cycle through all incident templates")
    parser.add_argument("--output", type=str, help="Write results JSON to file")
    args = parser.parse_args()

    print(c("\nSentinelAI Synthetic Incident Generator", Color.BOLD))
    print(info(f"API: {API_URL} | Count: {args.count} | Mode: {'async' if args.async_mode else 'sync'}\n"))

    results = []
    with get_client(timeout=180) as client:
        token = login(client)
        templates = INCIDENT_TEMPLATES if args.all_types else INCIDENT_TEMPLATES[: args.count]

        for i in range(args.count):
            template = templates[i % len(templates)]
            # Add uniqueness to avoid duplicate-title confusion in logs
            template = {**template, "title": f"{template['title']} [{uuid.uuid4().hex[:8]}]"}

            print(info(f"Generating: {template['title']}"))
            start = time.perf_counter()
            try:
                result = generate_incident(client, token, template, args.async_mode)
                elapsed = time.perf_counter() - start
                result["elapsed_seconds"] = round(elapsed, 2)
                results.append(result)
                print(
                    ok(
                        f"{result['id']} | {result['mode']} | "
                        f"status={result.get('status')} | {elapsed:.1f}s"
                    )
                )
                if result.get("root_cause"):
                    print(f"    Root cause: {result['root_cause'][:80]}...")
            except Exception as exc:
                print(fail(f"Failed: {exc}"))
                results.append({"error": str(exc), "title": template["title"]})

            if i < args.count - 1:
                time.sleep(1)

    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2))
        print(info(f"Results written to {args.output}"))

    failures = sum(1 for r in results if "error" in r)
    print()
    if failures:
        print(fail(f"{failures}/{len(results)} incidents failed"))
        return 1
    print(ok(f"Generated {len(results)} incident(s) successfully"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
