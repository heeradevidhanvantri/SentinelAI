import { getToken, removeToken } from "./auth";
import type {
  AgentFeedItem,
  HealthStatus,
  Incident,
  IncidentListResponse,
  PendingApproval,
  TokenResponse,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type UnauthorizedHandler = () => void;
let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
  unauthorizedHandler = handler;
}

async function parseErrorResponse(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item: { msg?: string }) => item.msg || String(item))
        .join(", ");
    }
    return data.message || res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  { auth = true }: { auth?: boolean } = {}
): Promise<T> {
  const token = auth ? getToken() : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401 && auth && token) {
    removeToken();
    unauthorizedHandler?.();
    throw new ApiError(401, "Session expired", "Authentication required");
  }

  if (!res.ok) {
    const detail = await parseErrorResponse(res);
    throw new ApiError(res.status, `API error: ${res.status}`, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    { auth: false }
  );
}

export const api = {
  getIncidents: (page = 1, pageSize = 20) =>
    apiFetch<IncidentListResponse>(
      `/api/v1/incidents?page=${page}&page_size=${pageSize}`
    ),

  getIncident: (id: string) =>
    apiFetch<Incident>(`/api/v1/incidents/${id}`),

  getAgentActivity: (limit = 50) =>
    apiFetch<{ feed: AgentFeedItem[] }>(
      `/api/v1/agents/activity?limit=${limit}`
    ),

  getMonitoringHealth: () =>
    apiFetch<HealthStatus[]>("/api/v1/monitoring/health"),

  getPendingApprovals: () =>
    apiFetch<PendingApproval[]>("/api/v1/remediation/pending"),

  getMe: () => apiFetch<{ id: string; email: string; role: string }>("/api/v1/auth/me"),
};
