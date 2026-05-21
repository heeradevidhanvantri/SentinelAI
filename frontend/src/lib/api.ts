import { getToken, removeToken } from "./auth";
import { buildApiUrl, getApiBaseUrl, getBackendUrl } from "./api-config";
import type {
  AgentFeedItem,
  HealthStatus,
  Incident,
  IncidentListResponse,
  PendingApproval,
  TokenResponse,
} from "./types";

export const API_URL = getBackendUrl();

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

function parseErrorBody(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const record = data as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  if (Array.isArray(record.detail)) {
    return record.detail
      .map((item) => {
        if (typeof item === "object" && item && "msg" in item) {
          return String((item as { msg?: string }).msg || item);
        }
        return String(item);
      })
      .join(", ");
  }
  if (typeof record.message === "string") return record.message;
  return fallback;
}

async function parseErrorResponse(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json();
    return parseErrorBody(data, res.statusText);
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
    console.error("[api] network error", {
      url,
      backend: getBackendUrl(),
      clientBase: getApiBaseUrl() || "(same-origin proxy)",
      error: err,
    });
    throw new ApiError(
      0,
      "Network error",
      `Cannot reach API at ${getBackendUrl()}. Check deployment configuration and network connectivity.`
    );
  }

  if (res.status === 401 && auth && token) {
    removeToken();
    unauthorizedHandler?.();
    throw new ApiError(401, "Session expired", "Authentication required");
  }

  if (!res.ok) {
    const detail = await parseErrorResponse(res);
    console.error("[api] error response", { url, status: res.status, detail });
    throw new ApiError(res.status, `API error: ${res.status}`, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

/**
 * Authenticate and return token payload.
 * Explicitly parses `access_token` from backend JSON response.
 */
export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const url = buildApiUrl("/api/v1/auth/login");

  console.info("[auth] login request", {
    url,
    backend: getBackendUrl(),
    clientBase: getApiBaseUrl() || "(same-origin proxy)",
    email,
  });

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ email, password }),
    });
  } catch (err) {
    console.error("[auth] network failure", { url, error: err });
    throw new ApiError(
      0,
      "Network error",
      `Cannot reach authentication service (${getBackendUrl()}). This is often caused by a missing API URL or CORS configuration.`
    );
  }

  const rawBody = await res.text();
  console.info("[auth] login response", {
    status: res.status,
    ok: res.ok,
    preview: rawBody.slice(0, 120),
  });

  let data: unknown;
  try {
    data = rawBody ? JSON.parse(rawBody) : null;
  } catch (err) {
    console.error("[auth] invalid JSON", { rawBody, error: err });
    throw new ApiError(
      res.status,
      "Invalid response",
      "Authentication service returned an invalid response."
    );
  }

  if (!res.ok) {
    const detail = parseErrorBody(data, res.statusText);
    console.error("[auth] login failed", { status: res.status, detail, data });
    throw new ApiError(res.status, "Login failed", detail);
  }

  const tokenResponse = data as TokenResponse;
  if (!tokenResponse?.access_token || typeof tokenResponse.access_token !== "string") {
    console.error("[auth] missing access_token", { data });
    throw new ApiError(
      res.status,
      "Invalid response",
      "Login succeeded but access_token was missing from the response."
    );
  }

  return tokenResponse;
}

export const api = {
  getIncidents: (page = 1, pageSize = 20) =>
    apiFetch<IncidentListResponse>(
      `/api/v1/incidents?page=${page}&page_size=${pageSize}`
    ),

  getIncident: (id: string) => apiFetch<Incident>(`/api/v1/incidents/${id}`),

  getAgentActivity: (limit = 50) =>
    apiFetch<{ feed: AgentFeedItem[] }>(`/api/v1/agents/activity?limit=${limit}`),

  getMonitoringHealth: () => apiFetch<HealthStatus[]>("/api/v1/monitoring/health"),

  getPendingApprovals: () =>
    apiFetch<PendingApproval[]>("/api/v1/remediation/pending"),

  getMe: () =>
    apiFetch<{ id: string; email: string; role: string }>("/api/v1/auth/me"),
};
