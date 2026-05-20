#!/usr/bin/env python3
"""Seed mock monitoring events into SentinelAI API."""

import json
import sys
from pathlib import Path

import httpx

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SAMPLES = Path(__file__).parent.parent / "samples" / "mock-events"


def main():
    # Login
    resp = httpx.post(
        f"{API_URL}/api/v1/auth/login",
        json={"email": "admin@sentinelai.io", "password": "sentinel123"},
    )
    token = resp.json().get("access_token", "")
    headers = {"Authorization": f"Bearer {token}"}

    for line in (SAMPLES / "metrics.jsonl").read_text().strip().split("\n"):
        if line:
            data = json.loads(line)
            httpx.post(
                f"{API_URL}/api/v1/monitoring/metrics/ingest",
                json={
                    "service": data["service"],
                    "metric_name": data["metric_name"],
                    "value": data["value"],
                },
                headers=headers,
            )
            print(f"Ingested metric: {data['metric_name']}")

    for line in (SAMPLES / "logs.jsonl").read_text().strip().split("\n"):
        if line:
            data = json.loads(line)
            httpx.post(
                f"{API_URL}/api/v1/monitoring/logs/ingest",
                json={
                    "service": data["service"],
                    "level": data["level"],
                    "message": data["message"],
                    "trace_id": data.get("trace_id"),
                },
                headers=headers,
            )
            print(f"Ingested log: {data['message'][:50]}")

    # Trigger pipeline
    resp = httpx.post(
        f"{API_URL}/api/v1/incidents/trigger",
        json={
            "title": "High error rate on payment-api",
            "description": "Error rate exceeded 3% threshold",
            "service": "payment-api",
            "severity": "critical",
        },
        headers=headers,
        timeout=180,
    )
    print(f"Triggered incident: {resp.json().get('id')}")


if __name__ == "__main__":
    main()
