"""Celery background tasks."""

import asyncio
from app.workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def run_incident_pipeline_task(self, incident_id: str, tenant_id: str):
    async def _run():
        from app.db.base import async_session_factory
        from app.services.incident import IncidentService

        async with async_session_factory() as db:
            service = IncidentService(db)
            incident = await service.get(incident_id, tenant_id)
            if incident:
                await service.run_pipeline(incident)
                await db.commit()

    try:
        run_async(_run())
        logger.info("pipeline_task_complete", incident_id=incident_id)
    except Exception as exc:
        logger.error("pipeline_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def execute_remediation_task(action_id: str):
    logger.info("remediation_execution", action_id=action_id)
    return {"action_id": action_id, "status": "executed"}


@celery_app.task
def ingest_metrics_batch(metrics: list[dict], tenant_id: str):
    logger.info("metrics_batch_ingested", count=len(metrics), tenant_id=tenant_id)
    return {"processed": len(metrics)}


@celery_app.task
def periodic_health_check():
    logger.info("periodic_health_check")
    return {"status": "ok"}
