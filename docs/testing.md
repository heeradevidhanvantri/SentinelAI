# SentinelAI Testing & Validation Guide

This document describes how to run automated tests, validation scripts, and demo tooling for the SentinelAI platform.

## Prerequisites

1. **Running stack** (for integration tests and validation scripts):
   ```bash
   docker compose up -d
   ```

2. **Test dependencies**:
   ```bash
   make install-test-deps
   # Windows:
   .\scripts\run-tests.ps1 install-test-deps
   ```

## Quick Reference

| Command | Description |
|---------|-------------|
| `make test` | Unit tests only (no Docker required) |
| `make test-all` | Full suite including integration |
| `make smoke-test` | Agent pipeline smoke tests |
| `make validate` | End-to-end platform validation |
| `make replay-demo` | Recruiter demo timeline |
| `make incidents` | Generate synthetic incidents |
| `make redis-diag` | Redis/Celery queue diagnostics |
| `make production-check` | Production readiness check |

Windows equivalents: `.\scripts\run-tests.ps1 <command>`

---

## Test Layers

### 1. Unit Tests (no infrastructure)

Run locally without Docker:

```bash
pytest -m "not integration"
# or
make test
```

**Covers:**
- Health endpoint (`/health` → `{"status":"ok"}`)
- LangGraph pipeline (Monitoring → Investigation → Decision → Execution → Reporting)
- Prometheus metric definitions
- Celery configuration (routes, beat schedule)
- Kafka producer graceful fallback

### 2. Integration Tests (requires running stack)

```bash
pytest -m integration
# or
make test-all
```

**Requires:** API, Redis, Kafka, Celery worker, Frontend (optional)

Integration tests auto-skip when services are unavailable.

### 3. End-to-End Validation Script

```bash
python scripts/test-platform.py
# or
make validate
```

**Validates:**
- Infrastructure: API, frontend, Redis, Postgres, Kafka, Prometheus
- Health: `GET /health`
- API flow: create incident → list → trigger pipeline → agent logs → evaluation
- Frontend: dashboard routes respond, backend reachable

**Environment variables:**

| Variable | Default |
|----------|---------|
| `SENTINEL_API_URL` | `http://localhost:8000` |
| `SENTINEL_FRONTEND_URL` | `http://localhost:3000` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` |
| `PROMETHEUS_URL` | `http://localhost:9090` |

**Docker usage:**
```bash
docker compose exec api python /app/../scripts/test-platform.py
# Or from host with defaults pointing to localhost ports
```

---

## Synthetic Incident Generator

```bash
# Single incident (sync pipeline)
python scripts/generate-incidents.py

# All incident types
python scripts/generate-incidents.py --all-types

# Async via Celery
python scripts/generate-incidents.py --all-types --async

# Save results
python scripts/generate-incidents.py -n 3 --output /tmp/incidents.json
```

**Incident types generated:**
- Kafka broker latency spike
- Kubernetes pod crash loop
- Redis connection saturation
- CPU exhaustion
- API timeout storm
- Postgres connection leak

Each incident ingests metrics/logs, creates an incident record, and triggers the agent pipeline.

---

## Demo Replay Simulator

For recruiter demos and presentations:

```bash
python scripts/demo-replay.py
# or
make replay-demo
```

**Timeline output:**
1. Alert generated
2. Incident created
3. Investigation starts
4. Root cause identified
5. Remediation selected
6. Action executed
7. Recovery validated
8. Report generated

Options:
- `--async` — use Celery async pipeline
- `--delay 1.2` — seconds between stages

---

## Redis & Celery Diagnostics

```bash
python scripts/redis-diagnostics.py
# or
make redis-diag
```

**Shows:**
- Redis memory usage
- Queue backlog (`default`, `execution`, `monitoring`)
- Celery worker status
- Active/scheduled/reserved tasks
- JSON output for scripting

---

## Production Readiness Check

```bash
python scripts/production-check.py
# or
make production-check
```

**Validates:**
- Required env vars (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, etc.)
- Optional integrations (OpenAI, Pinecone, OTEL)
- Redis, Kafka, Postgres, API, Frontend, Prometheus connectivity

---

## Architecture Validation Sequence

Recommended smoke test sequence after deployment:

```bash
# 1. Stack health
docker compose ps

# 2. Unit tests
make test

# 3. Platform validation
make validate

# 4. Pipeline smoke
make smoke-test

# 5. Demo replay
make replay-demo

# 6. Production check
make production-check
```

Or all at once:
```bash
make full-validation
```

---

## Test File Reference

| File | Purpose |
|------|---------|
| `backend/tests/test_health.py` | API health endpoint |
| `backend/tests/test_pipeline.py` | LangGraph agent pipeline |
| `backend/tests/test_celery.py` | Celery worker/broker/queues |
| `backend/tests/test_kafka.py` | Kafka producer/consumer |
| `backend/tests/test_observability.py` | Prometheus & OTEL metrics |
| `backend/tests/test_frontend_integration.py` | Frontend routes + API |
| `scripts/test-platform.py` | Full E2E validation |
| `scripts/generate-incidents.py` | Synthetic incidents |
| `scripts/demo-replay.py` | Demo timeline |
| `scripts/redis-diagnostics.py` | Queue diagnostics |
| `scripts/production-check.py` | Readiness check |

---

## Troubleshooting

### Integration tests skipped

```
SKIPPED [1] ... Redis not available
```

**Fix:** Start the stack: `docker compose up -d`

### Celery tests skipped

```
SKIPPED [1] ... No Celery workers running
```

**Fix:** Ensure `celery-worker` container is healthy:
```bash
docker compose logs celery-worker --tail 20
```

### Kafka consume test timeout

Kafka may need 60s cold start. Wait and retry:
```bash
docker compose ps kafka
pytest backend/tests/test_kafka.py -m integration -v
```

### Frontend integration failures

Frontend uses mock data internally; integration tests validate HTTP route availability and backend API connectivity separately.

### Auth for API tests

Demo credentials: `admin@sentinelai.io` / any password (demo mode).

---

## Coverage

```bash
make test-cov
# Report written to terminal; configure html output:
pytest -m "not integration" --cov=backend/app --cov-report=html
```

---

## CI Integration

Example GitHub Actions steps:

```yaml
- name: Unit tests
  run: pytest -m "not integration" --cov=backend/app

- name: Start stack
  run: docker compose up -d

- name: Wait for API
  run: |
    for i in $(seq 1 30); do
      curl -sf http://localhost:8000/health && break
      sleep 5
    done

- name: Platform validation
  run: python scripts/test-platform.py
```

---

## Expected Outputs

### Successful validation
```
✓ API reachable (45ms)
✓ Frontend reachable (120ms)
✓ Redis reachable (8ms)
...
All 12 checks passed
```

### Successful demo replay
```
[   800ms] Alert generated              service=payment-api
[  1600ms] Incident created             incident_id=abc-123
...
✓ Demo replay complete — ready for presentation
```

### Successful smoke test
```
backend/tests/test_pipeline.py::test_incident_pipeline_completes PASSED
backend/tests/test_pipeline.py::test_pipeline_agent_sequence PASSED
```
