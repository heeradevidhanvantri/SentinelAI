"""Monitoring API schemas."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class MetricIngest(BaseModel):
    service: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class LogIngest(BaseModel):
    service: str
    level: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class HealthStatus(BaseModel):
    service: str
    status: str
    latency_ms: float
    error_rate: float
    cpu_percent: float
    memory_percent: float
    last_check: datetime
