"""Incident API schemas."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.models.incident import IncidentStatus, IncidentSeverity


class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    service: str
    severity: IncidentSeverity = IncidentSeverity.HIGH
    metadata: Optional[dict[str, Any]] = None


class IncidentResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: Optional[str]
    status: IncidentStatus
    severity: IncidentSeverity
    service: Optional[str]
    root_cause: Optional[str]
    root_cause_confidence: Optional[float]
    remediation_plan: Optional[dict[str, Any]]
    resolution_time_seconds: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int


class TriggerPipelineRequest(BaseModel):
    incident_id: Optional[str] = None
    title: str
    description: str = ""
    service: str
    severity: IncidentSeverity = IncidentSeverity.HIGH


class ReasoningTraceResponse(BaseModel):
    id: str
    agent_name: str
    step: str
    reasoning: str
    tool_calls: Optional[list[dict]]
    tokens_used: Optional[float]
    latency_ms: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}
