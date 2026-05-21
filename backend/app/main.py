"""SentinelAI FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.config import get_settings
from app.core.auth import validate_jwt_config
from app.core.logging import setup_logging, get_logger
from app.core.observability import setup_telemetry, REQUEST_LATENCY
from app.api.v1 import api_router
from app.db.init_db import ensure_demo_user, init_database
from app.db.url import log_database_config
from app.services.kafka_producer import KafkaEventProducer

setup_logging()
logger = get_logger(__name__)
kafka_producer = KafkaEventProducer()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("sentinelai_starting", version=__version__, app_env=settings.app_env)

    jwt_warnings = validate_jwt_config()
    for warning in jwt_warnings:
        logger.warning("jwt_config_warning", detail=warning)

    log_database_config(settings.database_url)

    try:
        await init_database()
        await ensure_demo_user()
        logger.info("database_ready")
    except Exception:
        logger.exception("database_init_failed")
        if settings.app_env == "production":
            raise

    await kafka_producer.start()
    yield
    await kafka_producer.stop()
    logger.info("sentinelai_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Autonomous AI Site Reliability Engineering Platform",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        import time
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).observe(duration)
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "http_exception",
            path=request.url.path,
            status_code=exc.status_code,
            detail=exc.detail,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            request_id=request_id,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    app.include_router(api_router, prefix=settings.api_prefix)
    setup_telemetry(app)

    @app.get("/health")
    async def root_health():
        return {"status": "ok"}

    return app


app = create_app()
