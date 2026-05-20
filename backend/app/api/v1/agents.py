from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext, get_current_user
from app.db.base import get_db
from app.models.incident import ReasoningTrace

router = APIRouter()

AGENT_INFO = [
    {"name": "monitoring", "description": "Metrics, logs, anomaly detection", "status": "active"},
    {"name": "investigation", "description": "Root-cause analysis with RAG", "status": "active"},
    {"name": "decision", "description": "Remediation strategy selection", "status": "active"},
    {"name": "execution", "description": "Automated recovery actions", "status": "active"},
    {"name": "reporting", "description": "Incident reports and post-mortems", "status": "active"},
]


@router.get("")
async def list_agents(user: UserContext = Depends(get_current_user)):
    return {"agents": AGENT_INFO}


@router.get("/activity")
async def agent_activity_feed(
    limit: int = 50,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReasoningTrace)
        .where(ReasoningTrace.tenant_id == user.tenant_id)
        .order_by(ReasoningTrace.created_at.desc())
        .limit(limit)
    )
    traces = result.scalars().all()
    return {
        "feed": [
            {
                "id": t.id,
                "agent": t.agent_name,
                "step": t.step,
                "reasoning": t.reasoning[:300],
                "incident_id": t.incident_id,
                "latency_ms": t.latency_ms,
                "created_at": t.created_at.isoformat(),
            }
            for t in traces
        ]
    }


@router.get("/{incident_id}/timeline")
async def reasoning_timeline(
    incident_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ReasoningTrace)
        .where(
            ReasoningTrace.incident_id == incident_id,
            ReasoningTrace.tenant_id == user.tenant_id,
        )
        .order_by(ReasoningTrace.created_at.asc())
    )
    traces = result.scalars().all()
    return {
        "incident_id": incident_id,
        "timeline": [
            {
                "agent": t.agent_name,
                "step": t.step,
                "reasoning": t.reasoning,
                "tool_calls": t.tool_calls,
                "tokens_used": t.tokens_used,
                "latency_ms": t.latency_ms,
                "timestamp": t.created_at.isoformat(),
            }
            for t in traces
        ],
    }
