# SentinelAI Scaling Strategy

## Horizontal Scaling Targets

| Component | Min | Max | Trigger |
|-----------|-----|-----|---------|
| API (FastAPI) | 3 | 20 | CPU > 70% |
| Celery Workers | 4 | 50 | Queue depth > 100 |
| Frontend | 2 | 10 | CPU > 60% |
| Kafka Partitions | 6 | 24 | Throughput > 10k msg/s |

## API Layer

- Stateless FastAPI instances behind K8s Service + Ingress
- Connection pooling: 20 connections per instance (configurable)
- Redis for session cache and rate limiting
- CDN for frontend static assets

## Agent Pipeline Scaling

### Concurrent Incidents
- Each incident runs as independent LangGraph thread (checkpointed by `incident_id`)
- Celery `default` queue handles pipeline execution asynchronously
- Limit concurrent LLM calls per tenant via Redis semaphore

### LLM Cost Control
- Token usage tracked in Prometheus (`sentinelai_llm_tokens_total`)
- Per-tenant daily token budgets
- Model routing: GPT-4o for investigation, lighter models for monitoring summaries

## Data Layer Scaling

### PostgreSQL
- Read replicas for incident list queries
- Partition `metric_events` and `log_events` by month
- Connection pooler (PgBouncer) in production

### Pinecone
- Separate indexes per tenant for isolation
- Batch embedding ingestion during off-peak

### Kafka
- Partition by `tenant_id` for ordering guarantees
- Retention: 7 days metrics, 30 days incidents
- MSK with 3-broker minimum in production

## Event-Driven Architecture

```
Metrics → Kafka → Celery Consumer → Anomaly Detection → Incident Trigger
Logs    → Kafka → Aggregation → Investigation Context
Actions → Kafka → Audit Trail
```

## Multi-Region Strategy

1. **Active-Passive**: Primary region handles agent execution
2. **Traffic Reroute**: Execution agent supports cross-region failover
3. **Data Replication**: PostgreSQL cross-region read replicas
4. **Vector Store**: Pinecone serverless with regional pods

## Capacity Planning

| Scale | Incidents/day | Metrics/sec | Workers |
|-------|---------------|-------------|---------|
| Starter | 100 | 1,000 | 4 |
| Growth | 1,000 | 10,000 | 20 |
| Enterprise | 10,000 | 100,000 | 50+ |

## Performance SLOs

- API p99 latency: < 200ms (non-pipeline endpoints)
- Pipeline completion: < 15 minutes for P1 incidents
- Metric ingestion: < 5s end-to-end
- Dashboard refresh: < 2s
