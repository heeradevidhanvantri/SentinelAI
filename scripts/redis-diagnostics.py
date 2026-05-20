#!/usr/bin/env python3
"""Redis and Celery queue diagnostics for SentinelAI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _platform_utils import (  # noqa: E402
    REDIS_URL,
    c,
    fail,
    info,
    ok,
    Color,
)

CELERY_QUEUES = ["default", "execution", "monitoring", "celery"]


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != "B" else f"{n}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def inspect_redis() -> dict:
    import redis

    client = redis.from_url(REDIS_URL, decode_responses=True)
    info_data = client.info()

    queue_lengths = {}
    for queue in CELERY_QUEUES:
        queue_lengths[queue] = client.llen(queue)

    # Celery result keys pattern
    result_keys = len(list(client.scan_iter("celery-task-meta-*", count=100)))

    return {
        "redis_url": REDIS_URL,
        "memory_used": info_data.get("used_memory_human", "n/a"),
        "memory_peak": info_data.get("used_memory_peak_human", "n/a"),
        "connected_clients": info_data.get("connected_clients", 0),
        "total_commands": info_data.get("total_commands_processed", 0),
        "queue_lengths": queue_lengths,
        "celery_result_keys": result_keys,
        "uptime_seconds": info_data.get("uptime_in_seconds", 0),
    }


def inspect_celery() -> dict:
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
        from app.workers.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=5.0)
        return {
            "active_workers": list((inspect.active() or {}).keys()),
            "registered_tasks": {
                worker: tasks
                for worker, tasks in (inspect.registered() or {}).items()
            },
            "active_tasks": inspect.active() or {},
            "scheduled_tasks": inspect.scheduled() or {},
            "reserved_tasks": inspect.reserved() or {},
            "stats": inspect.stats() or {},
        }
    except Exception as exc:
        return {"error": str(exc)}


def print_section(title: str) -> None:
    print(c(f"\n{title}", Color.BOLD))
    print(c("-" * 40, Color.DIM))


def main() -> int:
    print(c("\nSentinelAI Redis & Celery Diagnostics", Color.BOLD))
    print(info(f"Redis: {REDIS_URL}"))

    try:
        redis_data = inspect_redis()
    except Exception as exc:
        print(fail(f"Redis connection failed: {exc}"))
        return 1

    print_section("Redis Memory & Connectivity")
    print(f"  Memory used:      {redis_data['memory_used']}")
    print(f"  Memory peak:      {redis_data['memory_peak']}")
    print(f"  Connected clients:{redis_data['connected_clients']}")
    print(f"  Uptime:           {redis_data['uptime_seconds']}s")
    print(f"  Commands processed:{redis_data['total_commands']}")

    print_section("Queue Backlog")
    total_backlog = 0
    for queue, length in redis_data["queue_lengths"].items():
        indicator = ok if length == 0 else c(f"{length} pending", Color.YELLOW)
        print(f"  {queue:12} {indicator}")
        total_backlog += length
    print(f"  Total backlog:    {total_backlog}")

    print_section("Celery Task Metadata")
    print(f"  Result keys:      {redis_data['celery_result_keys']}")

    print_section("Celery Workers")
    celery_data = inspect_celery()
    if "error" in celery_data:
        print(f"  {fail(celery_data['error'])}")
    else:
        workers = celery_data.get("active_workers", [])
        if workers:
            for worker in workers:
                stats = celery_data.get("stats", {}).get(worker, {})
                pool = stats.get("pool", {})
                print(ok(f"{worker} | pool={pool.get('implementation', 'n/a')} "
                         f"max={pool.get('max-concurrency', 'n/a')}"))
                active = celery_data.get("active_tasks", {}).get(worker, [])
                scheduled = celery_data.get("scheduled_tasks", {}).get(worker, [])
                print(f"    Active: {len(active)} | Scheduled: {len(scheduled)}")
        else:
            print(f"  {fail('No Celery workers responding')}")

    print()
    print(json.dumps({"redis": redis_data, "celery": celery_data}, indent=2, default=str))
    return 0 if "error" not in celery_data or redis_data else 1


if __name__ == "__main__":
    sys.exit(main())
