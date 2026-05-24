import { getToken, removeToken } from "./auth";
import { buildApiUrl, getBackendUrl } from "./api-config";
import { ApiError, parseErrorBody, parseJsonResponse } from "./http";
import type {
  AgentFeedItem,
  AuthUser,
  HealthStatus,
  Incident,
  IncidentListResponse,
  PendingApproval,
  TokenResponse,
} from "./types";

export { ApiError, formatApiError } from "./http";

type FetchOpts = {
  auth?: boolean;
  networkMessage?: string;
  errorTitle?: string;
};

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  { auth = true, networkMessage, errorTitle = "API error" }: FetchOpts = {}
): Promise<T> {
  const token = auth ? getToken() : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const url = buildApiUrl(path);

  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (err) {
    console.error("API network error", { url, err });
    throw new ApiError(
      0,
      "Network error",
      networkMessage ||
        `Cannot reach API at ${getBackendUrl()}. Check deployment configuration and network connectivity.`
    );
  }

  if (res.status === 401 && auth && token) {
    removeToken();
    onUnauthorized?.();
    throw new ApiError(401, "Session expired", "Authentication required");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      if (res.headers.get("content-type")?.includes("application/json")) {
        detail = parseErrorBody(await res.json(), res.statusText);
      } else {
        detail = (await res.text()).slice(0, 200) || res.statusText;
      }
    } catch {
      detail = res.statusText;
    }
    throw new ApiError(res.status, errorTitle, detail);
  }

  return parseJsonResponse<T>(res);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const data = await request<TokenResponse>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    {
      auth: false,
      networkMessage:
        "Authentication service is unavailable. Check your connection and try again.",
      errorTitle: "Login failed",
    }
  );

  if (!data?.access_token) {
    throw new ApiError(
      200,
      "Invalid response",
      "Login succeeded but access_token was missing from the response."
    );
  }

  return data;
}

export const api = {
  getIncidents: (page = 1, pageSize = 20) =>
    request<IncidentListResponse>(
      `/api/v1/incidents?page=${page}&page_size=${pageSize}`
    ),

  getIncident: (id: string) => request<Incident>(`/api/v1/incidents/${id}`),

  getAgentActivity: (limit = 50) =>
    request<{ feed: AgentFeedItem[] }>(`/api/v1/agents/activity?limit=${limit}`),

  getMonitoringHealth: () => request<HealthStatus[]>("/api/v1/monitoring/health"),

  getPendingApprovals: () =>
    request<PendingApproval[]>("/api/v1/remediation/pending"),

  getMe: () => request<AuthUser>("/api/v1/auth/me"),
};
