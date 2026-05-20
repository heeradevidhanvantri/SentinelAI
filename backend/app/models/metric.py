"""Metrics and log event models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Float, JSON, Text, Boolean

from app.db.base import Base


class MetricEvent(Base):
    __tablename__ = "metric_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    service = Column(String(128), nullable=False, index=True)
    metric_name = Column(String(128), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=True)
    labels = Column(JSON, nullable=True)
    is_anomaly = Column(Boolean, default=False)
    threshold_breached = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class LogEvent(Base):
    __tablename__ = "log_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    service = Column(String(128), nullable=False, index=True)
    level = Column(String(16), nullable=False, index=True)
    message = Column(Text, nullable=False)
    trace_id = Column(String(64), nullable=True, index=True)
    span_id = Column(String(32), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
