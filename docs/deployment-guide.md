# Production Deployment Guide

## Prerequisites

- AWS account with EKS, RDS, ElastiCache, MSK access
- Domain with TLS certificates (cert-manager)
- Container registry (GHCR recommended)
- OpenAI and Pinecone API keys

## Deployment Steps

### 1. Infrastructure (Terraform)

```bash
cd infrastructure/terraform
terraform init
terraform plan -var="environment=production"
terraform apply
```

Provisions:
- VPC with private subnets
- EKS cluster (3+ nodes)
- RDS PostgreSQL 16
- ElastiCache Redis
- MSK Kafka cluster

### 2. Configure Secrets

```bash
kubectl create namespace sentinelai

kubectl create secret generic sentinelai-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=PINECONE_API_KEY=... \
  --from-literal=JWT_SECRET_KEY=... \
  --from-literal=DATABASE_URL=postgresql+asyncpg://... \
  -n sentinelai
```

### 3. Deploy Application

```bash
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/
```

### 4. Database Migration

```bash
kubectl exec -it deploy/sentinelai-api -n sentinelai -- alembic upgrade head
```

### 5. Index Runbooks (RAG)

```bash
python scripts/index-runbooks.py
```

### 6. Verify Deployment

```bash
curl https://api.sentinelai.io/health
curl https://api.sentinelai.io/api/v1/metrics
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci-cd.yml`):

1. **Lint & Test**: ruff, mypy, pytest (backend); eslint, tsc, build (frontend)
2. **Security Scan**: Trivy filesystem scan
3. **Build & Push**: Docker images to GHCR on `main` push
4. **Deploy Staging**: kubectl rollout to `sentinelai-staging`
5. **Terraform Plan**: On pull requests

## Environment Configuration

| Variable | Production Value |
|----------|------------------|
| APP_ENV | production |
| DATABASE_URL | RDS connection string |
| REDIS_URL | ElastiCache endpoint |
| KAFKA_BOOTSTRAP_SERVERS | MSK broker list |
| CORS_ORIGINS | https://sentinelai.io |
| KUBERNETES_ENABLED | true |

## Scaling Checklist

- [ ] HPA configured for API (3-20 replicas)
- [ ] Celery workers scaled to 4+ per queue
- [ ] Kafka partitions >= 6
- [ ] RDS read replica for reporting queries
- [ ] Pinecone pod size appropriate for vector count

## Monitoring Setup

1. Deploy Prometheus via Helm or docker-compose config
2. Import Grafana dashboards from `infrastructure/grafana/`
3. Configure AlertManager PagerDuty integration
4. Enable OTEL collector sidecar on API pods

## Rollback Procedure

```bash
kubectl rollout undo deployment/sentinelai-api -n sentinelai
kubectl rollout undo deployment/sentinelai-frontend -n sentinelai
```

## Disaster Recovery

- RDS automated backups: 7-day retention
- Kafka topic replication factor: 3
- Pinecone vectors: export weekly to S3
- Incident data: PostgreSQL point-in-time recovery

## Security Hardening

- [ ] Network policies restrict pod-to-pod traffic
- [ ] Secrets rotated quarterly
- [ ] RBAC: least privilege for service accounts
- [ ] WAF on ingress
- [ ] Audit logs exported to SIEM

## Health Checks

| Endpoint | Expected |
|----------|----------|
| GET /health | 200 `{"status":"healthy"}` |
| GET /api/v1/metrics | Prometheus format |
| Agent pipeline test | Completes in < 120s |
