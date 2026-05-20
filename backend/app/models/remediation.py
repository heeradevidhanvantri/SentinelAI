"""Remediation action models."""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, JSON, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class RemediationStatus(str, Enum):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionType(str, Enum):
    K8S_POD_RESTART = "k8s_pod_restart"
    ECS_ROLLBACK = "ecs_rollback"
    AUTOSCALE = "autoscale"
    SERVICE_RESTART = "service_restart"
    TRAFFIC_REROUTE = "traffic_reroute"


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    status = Column(SQLEnum(RemediationStatus), default=RemediationStatus.PENDING)
    parameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="remediation_actions")
