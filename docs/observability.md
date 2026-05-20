# Observability Documentation

## Stack Overview

| Layer | Tool | Purpose |
|-------|------|---------|
| Metrics | Prometheus | API, agent, LLM token metrics |
| Dashboards | Grafana | SRE dashboards (Grafana-ready export) |
| Tracing | OpenTelemetry | Distributed request tracing |
| Logging | Structlog (JSON) | Structured application logs |
| Agent Logs | PostgreSQL | Reasoning trace persistence |

## Prometheus Metrics

### HTTP
- `sentinelai_http_request_duration_seconds` - Request latency histogram

### Agents
- `sentinelai_agent_invocations_total{agent, status}` - Agent call count
- `sentinelai_agent_duration_seconds{agent}` - Agent execution time
- `sentinelai_llm_tokens_total{model, type}` - Token usage

### Business
- `sentinelai_active_incidents{severity, tenant_id}` - Active incident gauge
- `sentinelai_remediation_success_total{action_type}` - Successful remediations
- `sentinelai_circuit_breaker_open{service}` - Circuit breaker state

## Grafana Dashboard Panels

Recommended panels:
1. Active incidents by severity (gauge)
2. Agent invocation rate (graph)
3. P99 API latency (graph)
4. LLM token usage per hour (graph)
5. Remediation success rate (stat)
6. Mean time to resolution (stat)

## OpenTelemetry

Configuration in `app/core/observability.py`:
- OTLP gRPC exporter to collector (port 4317)
- FastAPI auto-instrumentation
- Service name: `sentinelai-api`

Collector config: `infrastructure/otel/otel-collector.yml`

### Trace Context Propagation

Pass `trace_id` in log ingestion for correlation:
```
Log → trace_id → Investigation Agent → Reasoning Trace
```

## Agent Reasoning Logs

Stored in `reasoning_traces` table:
- `agent_name`, `step`, `reasoning`
- `tool_calls` (JSON)
- `tokens_used`, `latency_ms`

Accessible via:
- `GET /api/v1/agents/activity` - Live feed
- `GET /api/v1/agents/{incident_id}/timeline` - Per-incident timeline

## Structured Logging

```python
logger.info("pipeline_complete", incident_id=id, status=status)
```

Fields: timestamp (ISO), level, event name, context key-values.

## Alerting Rules

Example Prometheus alerts (`infrastructure/prometheus/alerts.yml`):

```yaml
- alert: HighErrorRate
  expr: sentinelai_active_incidents{severity="critical"} > 0
  for: 1m

- alert: AgentPipelineSlow
  expr: histogram_quantile(0.99, sentinelai_agent_duration_seconds) > 120
  for: 5m
```

## Local Development

```bash
# View metrics
curl http://localhost:8000/api/v1/metrics

# Prometheus UI
open http://localhost:9090
```
