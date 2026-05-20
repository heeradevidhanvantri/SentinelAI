from fastapi import APIRouter, Response

from app import __version__
from app.core.observability import metrics_response

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": __version__, "service": "sentinelai-api"}


@router.get("/metrics")
async def prometheus_metrics():
    content, content_type = metrics_response()
    return Response(content=content, media_type=content_type)
