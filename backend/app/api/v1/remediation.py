from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, require_role, Role
from app.core.audit import log_audit
from app.db.base import get_db
from app.models.remediation import RemediationAction, RemediationStatus
from app.workers.tasks import execute_remediation_task

router = APIRouter()


@router.get("/pending")
async def list_pending_approvals(
    user: UserContext = Depends(require_role(Role.OPERATOR, Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RemediationAction).where(
            RemediationAction.tenant_id == user.tenant_id,
            RemediationAction.status == RemediationStatus.AWAITING_APPROVAL,
        )
    )
    actions = result.scalars().all()
    return [
        {
            "id": a.id,
            "incident_id": a.incident_id,
            "action_type": a.action_type.value,
            "parameters": a.parameters,
            "created_at": a.created_at.isoformat(),
        }
        for a in actions
    ]


@router.post("/{action_id}/approve")
async def approve_remediation(
    action_id: str,
    user: UserContext = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RemediationAction).where(
            RemediationAction.id == action_id,
            RemediationAction.tenant_id == user.tenant_id,
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.status = RemediationStatus.APPROVED
    action.approved_by = user.user_id
    action.approved_at = datetime.now(timezone.utc)
    await log_audit(db, user.tenant_id, "remediation.approve", "remediation", user.user_id, action_id)

    execute_remediation_task.delay(action_id)
    return {"status": "approved", "action_id": action_id}


@router.post("/{action_id}/reject")
async def reject_remediation(
    action_id: str,
    user: UserContext = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RemediationAction).where(
            RemediationAction.id == action_id,
            RemediationAction.tenant_id == user.tenant_id,
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.status = RemediationStatus.FAILED
    action.error_message = "Rejected by operator"
    await log_audit(db, user.tenant_id, "remediation.reject", "remediation", user.user_id, action_id)
    return {"status": "rejected"}
