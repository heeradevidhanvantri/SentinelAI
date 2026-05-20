"""OpenTelemetry and Prometheus instrumentation."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Prometheus metrics
REQUEST_LATENCY = Histogram(
    "sentinelai_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
AGENT_INVOCATIONS = Counter(
    "sentinelai_agent_invocations_total",
    "Total agent invocations",
    ["agent", "status"],
)
AGENT_LATENCY = Histogram(
    "sentinelai_agent_duration_seconds",
    "Agent execution duration",
    ["agent"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)
TOKEN_USAGE = Counter(
    "sentinelai_llm_tokens_total",
    "LLM token usage",
    ["model", "type"],
)
ACTIVE_INCIDENTS = Gauge(
    "sentinelai_active_incidents",
    "Number of active incidents",
    ["severity", "tenant_id"],
)
REMEDIATION_SUCCESS = Counter(
    "sentinelai_remediation_success_total",
    "Successful remediation actions",
    ["action_type"],
)
CIRCUIT_BREAKER_STATE = Gauge(
    "sentinelai_circuit_breaker_open",
    "Circuit breaker state (1=open)",
    ["service"],
)


def setup_telemetry(app) -> None:
    """Configure OpenTelemetry for FastAPI."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from app.config import get_settings

        settings = get_settings()
        provider = TracerProvider()
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass  # OTEL optional in dev


def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST
