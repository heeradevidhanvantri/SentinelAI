# SentinelAI Architecture

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Clients
        UI[Next.js Dashboard]
        API_C[External Integrations]
    end

    subgraph API_Layer[API Layer]
        FastAPI[FastAPI Gateway]
        Auth[JWT + RBAC]
    end

    subgraph Agent_Layer[AI Agent Layer - LangGraph]
        MA[Monitoring Agent]
        IA[Investigation Agent]
        DA[Decision Agent]
        EA[Execution Agent]
        RA[Reporting Agent]
        State[(Shared Graph State)]
    end

    subgraph Data_Layer[Data Layer]
        PG[(PostgreSQL)]
        Redis[(Redis)]
        Pinecone[(Pinecone)]
        Kafka[[Kafka]]
    end

    subgraph Workers
        Celery[Celery Workers]
    end

    subgraph Observability
        Prom[Prometheus]
        OTEL[OpenTelemetry]
        Grafana[Grafana]
    end

    UI --> FastAPI
    API_C --> FastAPI
    FastAPI --> Auth
    FastAPI --> MA
    MA --> State
    State --> IA --> DA --> EA --> RA
    FastAPI --> PG
    FastAPI --> Redis
    IA --> Pinecone
    FastAPI --> Kafka
    Celery --> Kafka
    Celery --> PG
    EA --> K8s[Kubernetes]
    EA --> ECS[AWS ECS]
    FastAPI --> OTEL
    OTEL --> Prom
    Prom --> Grafana
```

## Component Responsibilities

### Frontend (Next.js 15)
- Enterprise dark-theme operations dashboard
- Live incident management
- Agent activity feed and reasoning timeline
- Infrastructure health panel
- Remediation approval workflow
- Analytics with Recharts

### Backend (FastAPI)
- REST API with typed Pydantic schemas
- JWT authentication with RBAC (viewer, operator, admin)
- Multi-tenant data isolation
- Audit logging for compliance

### AI Agents (LangGraph)
All agents communicate through `IncidentGraphState`:

| Agent | Input | Output |
|-------|-------|--------|
| Monitoring | Metrics, logs, traces | Anomalies, threshold alerts, latency issues |
| Investigation | Monitoring output + RAG | Root cause hypothesis, confidence score |
| Decision | Investigation output | Remediation plans, risk assessment |
| Execution | Selected plan | Action results, rollback flag |
| Reporting | Full pipeline state | Incident report, post-mortem |

### Event Streaming (Kafka)
Topics: `sentinel.metrics`, `sentinel.logs`, `sentinel.incidents`, `sentinel.actions`

### Task Queue (Celery + Redis)
Queues: `default`, `execution`, `monitoring`

## Data Flow

1. **Ingestion**: Metrics/logs arrive via API or Kafka
2. **Detection**: Anomaly detector flags outliers; thresholds trigger alerts
3. **Incident Creation**: Alert creates incident record in PostgreSQL
4. **Pipeline**: LangGraph executes 5-agent workflow with shared state
5. **Approval**: High-risk actions require operator approval
6. **Execution**: Celery workers execute infrastructure actions
7. **Reporting**: Final agent generates incident report and evaluation scores

## Security Architecture

- JWT tokens with tenant_id and role claims
- Row-level tenant isolation on all queries
- Audit log for all state-changing operations
- Remediation approval gate for production actions
- Secrets via K8s Secrets / AWS Secrets Manager
