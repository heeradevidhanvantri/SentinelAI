"""Celery application configuration."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sentinelai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    result_backend_transport_options={
        "retry_policy": {
            "timeout": 5.0,
            "max_retries": 10,
        }
    },
    task_routes={
        "app.workers.tasks.run_incident_pipeline_task": {"queue": "default"},
        "app.workers.tasks.execute_remediation_task": {"queue": "execution"},
        "app.workers.tasks.ingest_metrics_batch": {"queue": "monitoring"},
    },
    beat_schedule={
        "health-check-every-60s": {
            "task": "app.workers.tasks.periodic_health_check",
            "schedule": 60.0,
        },
    },
)
