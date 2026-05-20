"""SentinelAI FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.observability import setup_telemetry, REQUEST_LATENCY
from app.api.v1 import api_router
from app.services.kafka_producer import KafkaEventProducer

setup_logging()
logger = get_logger(__name__)
kafka_producer = KafkaEventProducer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("sentinelai_starting", version=__version__)
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

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(api_router, prefix=settings.api_prefix)
    setup_telemetry(app)

    @app.get("/health")
    async def root_health():
        return {"status": "ok"}

    return app


app = create_app()
