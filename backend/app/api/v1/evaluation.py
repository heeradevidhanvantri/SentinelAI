from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import UserContext, require_role, Role
from app.services.evaluation import EvaluationFramework

router = APIRouter()
evaluator = EvaluationFramework()


class EvaluateRequest(BaseModel):
    predicted_root_cause: str
    actual_root_cause: str | None = None
    execution_success: bool
    resolution_time_seconds: float
    reasoning_traces: list[dict] = []


@router.post("/score")
async def score_incident(
    data: EvaluateRequest,
    user: UserContext = Depends(require_role(Role.ADMIN)),
):
    result = evaluator.evaluate_incident(
        predicted_root_cause=data.predicted_root_cause,
        actual_root_cause=data.actual_root_cause,
        execution_success=data.execution_success,
        resolution_time_seconds=data.resolution_time_seconds,
        reasoning_traces=data.reasoning_traces,
    )
    return {
        "hallucination_score": result.hallucination_score,
        "root_cause_accuracy": result.root_cause_accuracy,
        "remediation_success": result.remediation_success,
        "resolution_time_seconds": result.resolution_time_seconds,
        "overall_score": result.overall_score,
        "details": result.details,
    }
