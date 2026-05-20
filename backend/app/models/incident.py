"""Incident domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, JSON, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.db.base import Base


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    ANALYZING = "analyzing"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN, index=True)
    severity = Column(SQLEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM, index=True)
    service = Column(String(128), nullable=True, index=True)
    root_cause = Column(Text, nullable=True)
    root_cause_confidence = Column(Float, nullable=True)
    remediation_plan = Column(JSON, nullable=True)
    resolution_time_seconds = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    reasoning_traces = relationship("ReasoningTrace", back_populates="incident", lazy="selectin")
    remediation_actions = relationship("RemediationAction", back_populates="incident", lazy="selectin")


class ReasoningTrace(Base):
    __tablename__ = "reasoning_traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False)
    agent_name = Column(String(64), nullable=False, index=True)
    step = Column(String(128), nullable=False)
    reasoning = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    tokens_used = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="reasoning_traces")
