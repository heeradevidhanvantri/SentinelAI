export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  tenant_id: string;
  role: string;
}

export interface Incident {
  id: string;
  tenant_id: string;
  title: string;
  description?: string | null;
  status: string;
  severity: string;
  service?: string | null;
  root_cause?: string | null;
  root_cause_confidence?: number | null;
  remediation_plan?: Record<string, unknown> | null;
  resolution_time_seconds?: number | null;
  created_at: string;
  updated_at?: string | null;
  resolved_at?: string | null;
}

export interface IncidentListResponse {
  items: Incident[];
  total: number;
  page: number;
  page_size: number;
}

export interface AgentFeedItem {
  id: string;
  agent: string;
  step: string;
  reasoning: string;
  incident_id: string;
  latency_ms?: number;
  created_at: string;
}

export interface HealthStatus {
  service: string;
  status: string;
  latency_ms: number;
  error_rate: number;
  cpu_percent: number;
  memory_percent: number;
  last_check?: string;
}

export interface PendingApproval {
  id: string;
  incident_id: string;
  action_type: string;
  parameters: Record<string, unknown>;
  created_at: string;
}
