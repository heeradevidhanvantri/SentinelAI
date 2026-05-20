export const mockIncidents = [
  {
    id: "inc-001",
    title: "High error rate on payment-api",
    service: "payment-api",
    severity: "critical",
    status: "investigating",
    root_cause: "Database connection pool exhaustion",
    root_cause_confidence: 0.87,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "inc-002",
    title: "Elevated latency on notification-worker",
    service: "notification-worker",
    severity: "high",
    status: "remediating",
    root_cause: "Kafka consumer lag",
    root_cause_confidence: 0.72,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: "inc-003",
    title: "Auth service intermittent 503s",
    service: "auth-service",
    severity: "medium",
    status: "resolved",
    root_cause: "Certificate rotation timeout",
    root_cause_confidence: 0.95,
    created_at: new Date(Date.now() - 86400000).toISOString(),
    resolution_time_seconds: 480,
  },
];

export const mockAgentFeed = [
  { id: "1", agent: "monitoring", step: "anomaly_detection", reasoning: "Detected error_rate spike to 3.2% exceeding 1% threshold", incident_id: "inc-001", latency_ms: 1240, created_at: new Date().toISOString() },
  { id: "2", agent: "investigation", step: "root_cause_analysis", reasoning: "Correlated pool exhaustion with analytics query deployment at 14:32 UTC", incident_id: "inc-001", latency_ms: 3420, created_at: new Date().toISOString() },
  { id: "3", agent: "decision", step: "remediation_selection", reasoning: "Selected k8s_pod_restart with autoscale fallback. Risk: low.", incident_id: "inc-001", latency_ms: 2100, created_at: new Date().toISOString() },
  { id: "4", agent: "execution", step: "action_execute", reasoning: "Restarted payment-api-0 pod. Triggered autoscale to 5 replicas.", incident_id: "inc-001", latency_ms: 5600, created_at: new Date().toISOString() },
];

export const mockHealth = [
  { service: "payment-api", status: "degraded", latency_ms: 245, error_rate: 3.2, cpu_percent: 78, memory_percent: 65 },
  { service: "auth-service", status: "healthy", latency_ms: 45, error_rate: 0.1, cpu_percent: 32, memory_percent: 48 },
  { service: "order-processor", status: "healthy", latency_ms: 120, error_rate: 0.5, cpu_percent: 55, memory_percent: 72 },
  { service: "notification-worker", status: "critical", latency_ms: 890, error_rate: 12.5, cpu_percent: 95, memory_percent: 88 },
];

export const chartData = [
  { time: "00:00", errors: 0.2, latency: 45, incidents: 0 },
  { time: "04:00", errors: 0.3, latency: 52, incidents: 0 },
  { time: "08:00", errors: 0.5, latency: 68, incidents: 1 },
  { time: "12:00", errors: 1.2, latency: 120, incidents: 2 },
  { time: "14:00", errors: 3.2, latency: 450, incidents: 3 },
  { time: "16:00", errors: 2.1, latency: 280, incidents: 2 },
  { time: "20:00", errors: 0.8, latency: 95, incidents: 1 },
];

export const pendingApprovals = [
  { id: "rem-001", incident_id: "inc-001", action_type: "k8s_pod_restart", parameters: { namespace: "production", pod_name: "payment-api-0" }, created_at: new Date().toISOString() },
];
