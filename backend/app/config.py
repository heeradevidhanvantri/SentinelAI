"""Application configuration with environment-based settings."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "SentinelAI"
    app_version: str = "1.0.0"
    secret_key: str = Field(default="change-me-in-production")
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinelai"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_metrics: str = "sentinel.metrics"
    kafka_topic_logs: str = "sentinel.logs"
    kafka_topic_incidents: str = "sentinel.incidents"
    kafka_topic_actions: str = "sentinel.actions"
    kafka_consumer_group: str = "sentinel-workers"

    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1-aws"
    pinecone_index: str = "sentinelai-runbooks"
    pinecone_dimension: int = 1536

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    agent_max_retries: int = 3
    agent_timeout_seconds: int = 120

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "sentinelai-api"
    prometheus_port: int = 9090
    log_level: str = "INFO"

    jwt_secret_key: str = Field(default="change-me-jwt-secret")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3000"
    kubernetes_enabled: bool = False
    ecs_enabled: bool = False

    default_tenant_id: str = "default"
    tenant_isolation_enabled: bool = True

    @property
    def normalized_database_url(self) -> str:
        from app.db.url import normalize_database_url
        return normalize_database_url(self.database_url)

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
