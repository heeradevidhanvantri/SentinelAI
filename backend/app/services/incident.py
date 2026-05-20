"""Incident management service."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import run_incident_pipeline
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, ReasoningTrace
from app.schemas.incident import IncidentCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


class IncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: str, data: IncidentCreate) -> Incident:
        incident = Incident(
            id=str(uuid4()),
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            service=data.service,
            severity=data.severity,
            status=IncidentStatus.OPEN,
            metadata_=data.metadata,
        )
        self.db.add(incident)
        await self.db.flush()
        return incident

    async def get(self, incident_id: str, tenant_id: str) -> Optional[Incident]:
        result = await self.db.execute(
            select(Incident).where(
                Incident.id == incident_id,
                Incident.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[IncidentStatus] = None,
    ) -> tuple[list[Incident], int]:
        query = select(Incident).where(Incident.tenant_id == tenant_id)
        count_query = select(func.count()).select_from(Incident).where(
            Incident.tenant_id == tenant_id
        )
        if status:
            query = query.where(Incident.status == status)
            count_query = count_query.where(Incident.status == status)

        total = (await self.db.execute(count_query)).scalar() or 0
        result = await self.db.execute(
            query.order_by(Incident.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def run_pipeline(self, incident: Incident) -> Incident:
        start = datetime.now(timezone.utc)
        incident.status = IncidentStatus.INVESTIGATING
        await self.db.flush()

        final_state = await run_incident_pipeline(
            incident_id=incident.id,
            tenant_id=incident.tenant_id,
            alert_title=incident.title,
            alert_description=incident.description or "",
            service=incident.service or "unknown",
            severity=incident.severity.value if incident.severity else "high",
        )

        incident.root_cause = final_state.get("root_cause_hypothesis")
        incident.root_cause_confidence = final_state.get("root_cause_confidence")
        incident.remediation_plan = final_state.get("selected_plan")
        incident.status = (
            IncidentStatus.RESOLVED
            if final_state.get("execution_success")
            else IncidentStatus.REMEDIATING
        )
        if incident.status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)
            incident.resolution_time_seconds = (
                incident.resolved_at - start
            ).total_seconds()

        for trace in final_state.get("reasoning_traces", []):
            self.db.add(ReasoningTrace(
                id=str(uuid4()),
                incident_id=incident.id,
                tenant_id=incident.tenant_id,
                agent_name=trace.get("agent", "unknown"),
                step=trace.get("step", ""),
                reasoning=trace.get("reasoning", ""),
                tool_calls=trace.get("tool_calls"),
                tokens_used=trace.get("tokens_used"),
                latency_ms=trace.get("latency_ms"),
            ))

        await self.db.flush()
        return incident
