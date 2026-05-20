"""Celery worker, broker, and queue validation tests."""

from __future__ import annotations

import os

import pytest

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _redis_available() -> bool:
    try:
        import redis
        return bool(redis.from_url(REDIS_URL).ping())
    except Exception:
        return False


def _celery_workers_available() -> bool:
    try:
        from app.workers.celery_app import celery_app
        inspect = celery_app.control.inspect(timeout=3.0)
        return bool(inspect.ping())
    except Exception:
        return False


@pytest.mark.integration
def test_redis_broker_connectivity():
    if not _redis_available():
        pytest.skip("Redis not available")
    import redis
    client = redis.from_url(REDIS_URL)
    assert client.ping()


@pytest.mark.integration
def test_celery_app_configuration():
    from app.workers.celery_app import celery_app
    from app.config import get_settings

    settings = get_settings()
    assert "redis" in celery_app.conf.broker_url
    assert celery_app.conf.broker_url == settings.celery_broker_url
    assert celery_app.conf.result_backend == settings.celery_result_backend
    assert celery_app.conf.broker_connection_retry_on_startup is True


@pytest.mark.integration
def test_celery_task_routes():
    from app.workers.celery_app import celery_app

    routes = celery_app.conf.task_routes
    assert "app.workers.tasks.run_incident_pipeline_task" in routes
    assert routes["app.workers.tasks.run_incident_pipeline_task"]["queue"] == "default"
    assert routes["app.workers.tasks.execute_remediation_task"]["queue"] == "execution"
    assert routes["app.workers.tasks.ingest_metrics_batch"]["queue"] == "monitoring"


@pytest.mark.integration
def test_celery_beat_schedule():
    from app.workers.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule
    assert "health-check-every-60s" in schedule
    assert schedule["health-check-every-60s"]["task"] == "app.workers.tasks.periodic_health_check"


@pytest.mark.integration
@pytest.mark.skipif(not _celery_workers_available(), reason="No Celery workers running")
def test_celery_worker_ping():
    from app.workers.celery_app import celery_app

    inspect = celery_app.control.inspect(timeout=5.0)
    ping = inspect.ping()
    assert ping is not None
    assert len(ping) >= 1


@pytest.mark.integration
@pytest.mark.skipif(not _celery_workers_available(), reason="No Celery workers running")
def test_periodic_health_check_task():
    from app.workers.tasks import periodic_health_check

    result = periodic_health_check.delay()
    output = result.get(timeout=30)
    assert output == {"status": "ok"}


@pytest.mark.integration
@pytest.mark.skipif(not _celery_workers_available(), reason="No Celery workers running")
def test_execute_remediation_task():
    from app.workers.tasks import execute_remediation_task

    result = execute_remediation_task.delay("test-action-001")
    output = result.get(timeout=30)
    assert output["status"] == "executed"
    assert output["action_id"] == "test-action-001"


@pytest.mark.integration
@pytest.mark.skipif(not _celery_workers_available(), reason="No Celery workers running")
def test_ingest_metrics_batch_task():
    from app.workers.tasks import ingest_metrics_batch

    metrics = [{"service": "test", "metric_name": "cpu", "value": 85.0}]
    result = ingest_metrics_batch.delay(metrics, "default")
    output = result.get(timeout=30)
    assert output["processed"] == 1


@pytest.mark.integration
@pytest.mark.skipif(not _redis_available(), reason="Redis not available")
def test_celery_queue_lengths():
    import redis

    client = redis.from_url(REDIS_URL)
    for queue in ("default", "execution", "monitoring"):
        length = client.llen(queue)
        assert length >= 0
