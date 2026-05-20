"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, incidents, monitoring, remediation, agents, evaluation, health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(remediation.router, prefix="/remediation", tags=["remediation"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
