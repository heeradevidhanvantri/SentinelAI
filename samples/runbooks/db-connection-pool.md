# Database Connection Pool Exhaustion

## Symptoms
- Error rate spike on API services
- `Connection is not available, request timed out` in logs
- `HikariPool` or connection pool metrics at 98%+ utilization

## Diagnosis
1. Check `db_connections_active` metric in Prometheus
2. Search logs for `pool exhausted`, `connection timeout`
3. Identify long-running queries via `pg_stat_activity`

## Remediation
1. **Immediate**: Restart affected pods (`kubectl rollout restart deployment/<service>`)
2. **Scale**: Increase read replicas or connection pool max size
3. **Query**: Kill long-running analytics queries
4. **Verify**: Error rate < 1% within 5 minutes

## Prevention
- Set query timeouts on analytics workloads
- Alert at 80% pool utilization
- Separate read/write connection pools

## Blast Radius
payment-processing, checkout flow
