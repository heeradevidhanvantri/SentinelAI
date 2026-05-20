# Payment Service Architecture

## Overview
The payment-api service handles card charges, refunds, and subscription billing.

## Dependencies
- **PostgreSQL** (payment-db): Primary transactional store
- **Redis**: Session cache, idempotency keys
- **Kafka**: Event publishing for order-processor
- **Stripe API**: External payment processor

## SLA
- Availability: 99.9%
- P99 Latency: < 200ms
- Error Rate: < 1%

## Deployment
- Kubernetes namespace: `production`
- Replicas: 3-10 (HPA on CPU 70%)
- Regions: us-east-1, eu-west-1

## On-Call
- Primary: platform-team
- Escalation: payments-sre

## Known Failure Modes
1. Connection pool exhaustion (see runbook)
2. Stripe API rate limiting
3. Kafka producer backpressure
