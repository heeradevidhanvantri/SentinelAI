from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user, require_role, Role
from app.db.base import get_db
from app.models.metric import MetricEvent, LogEvent
from app.schemas.monitoring import MetricIngest, LogIngest, HealthStatus
from app.services.anomaly import AnomalyDetector
from app.services.kafka_producer import KafkaEventProducer

router = APIRouter()
anomaly_detector = AnomalyDetector()
kafka = KafkaEventProducer()


@router.post("/metrics/ingest")
async def ingest_metric(
    data: MetricIngest,
    user: UserContext = Depends(require_role(Role.OPERATOR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    detection = anomaly_detector.detect(data.value)
    event = MetricEvent(
        id=str(uuid4()),
        tenant_id=user.tenant_id,
        service=data.service,
        metric_name=data.metric_name,
        value=data.value,
        unit=data.unit,
        labels=data.labels,
        is_anomaly=detection["is_anomaly"],
        threshold_breached=anomaly_detector.check_threshold(data.value, 100),
        timestamp=data.timestamp or datetime.now(timezone.utc),
    )
    db.add(event)
    await kafka.publish_metric(user.tenant_id, {
        "service": data.service,
        "metric": data.metric_name,
        "value": data.value,
        "is_anomaly": detection["is_anomaly"],
    })
    return {"id": event.id, "is_anomaly": detection["is_anomaly"]}


@router.post("/logs/ingest")
async def ingest_log(
    data: LogIngest,
    user: UserContext = Depends(require_role(Role.OPERATOR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    event = LogEvent(
        id=str(uuid4()),
        tenant_id=user.tenant_id,
        service=data.service,
        level=data.level,
        message=data.message,
        trace_id=data.trace_id,
        span_id=data.span_id,
        metadata_=data.metadata,
        timestamp=data.timestamp or datetime.now(timezone.utc),
    )
    db.add(event)
    return {"id": event.id}


@router.get("/health", response_model=list[HealthStatus])
async def infrastructure_health(
    user: UserContext = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    return [
        HealthStatus(
            service="payment-api",
            status="degraded",
            latency_ms=245,
            error_rate=3.2,
            cpu_percent=78,
            memory_percent=65,
            last_check=now,
        ),
        HealthStatus(
            service="auth-service",
            status="healthy",
            latency_ms=45,
            error_rate=0.1,
            cpu_percent=32,
            memory_percent=48,
            last_check=now,
        ),
        HealthStatus(
            service="order-processor",
            status="healthy",
            latency_ms=120,
            error_rate=0.5,
            cpu_percent=55,
            memory_percent=72,
            last_check=now,
        ),
        HealthStatus(
            service="notification-worker",
            status="critical",
            latency_ms=890,
            error_rate=12.5,
            cpu_percent=95,
            memory_percent=88,
            last_check=now,
        ),
    ]
