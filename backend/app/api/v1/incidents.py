from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user, require_role, Role
from app.core.audit import log_audit
from app.db.base import get_db
from app.models.incident import IncidentStatus
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentListResponse,
    TriggerPipelineRequest,
)
from app.services.incident import IncidentService
from app.workers.tasks import run_incident_pipeline_task

router = APIRouter()


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: IncidentStatus | None = None,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IncidentService(db)
    items, total = await service.list(user.tenant_id, page, page_size, status)
    return IncidentListResponse(
        items=[IncidentResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=IncidentResponse)
async def create_incident(
    data: IncidentCreate,
    user: UserContext = Depends(require_role(Role.OPERATOR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = IncidentService(db)
    incident = await service.create(user.tenant_id, data)
    await log_audit(db, user.tenant_id, "incident.create", "incident", user.user_id, incident.id)
    return IncidentResponse.model_validate(incident)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = IncidentService(db)
    incident = await service.get(incident_id, user.tenant_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/investigate", response_model=IncidentResponse)
async def trigger_investigation(
    incident_id: str,
    user: UserContext = Depends(require_role(Role.OPERATOR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = IncidentService(db)
    incident = await service.get(incident_id, user.tenant_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    run_incident_pipeline_task.delay(incident_id, user.tenant_id)
    await log_audit(db, user.tenant_id, "incident.investigate", "incident", user.user_id, incident_id)
    return IncidentResponse.model_validate(incident)


@router.post("/trigger", response_model=IncidentResponse)
async def trigger_pipeline(
    data: TriggerPipelineRequest,
    user: UserContext = Depends(require_role(Role.OPERATOR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = IncidentService(db)
    incident = await service.create(
        user.tenant_id,
        IncidentCreate(
            title=data.title,
            description=data.description,
            service=data.service,
            severity=data.severity,
        ),
    )
    incident = await service.run_pipeline(incident)
    return IncidentResponse.model_validate(incident)
