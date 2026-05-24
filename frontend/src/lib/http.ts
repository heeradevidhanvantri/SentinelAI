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

export async function parseJsonResponse<T>(res: Response): Promise<T> {
  const contentType = res.headers.get("content-type")?.toLowerCase() ?? "";

  if (!contentType.includes("application/json")) {
    const body = await res.text();
    console.error("non-JSON API response", {
      status: res.status,
      contentType,
      url: res.url,
      body: body.slice(0, 500),
    });

    const detail = contentType.includes("text/html")
      ? "Received HTML instead of JSON — the API route may be missing or misconfigured."
      : `Unexpected content-type: ${contentType || "unknown"}`;

    throw new ApiError(res.status, "Invalid response", detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  try {
    return (await res.json()) as T;
  } catch (err) {
    console.error("JSON parse failed", { status: res.status, url: res.url, err });
    throw new ApiError(res.status, "Invalid JSON", "Server returned malformed JSON.");
  }
}

export function parseErrorBody(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const record = data as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  if (Array.isArray(record.detail)) {
    return record.detail.map(String).join(", ");
  }
  if (typeof record.message === "string") return record.message;
  return fallback;
}

export function formatApiError(err: unknown, fallback = "Request failed"): string {
  if (err instanceof ApiError) {
    if (err.status === 0) {
      return err.detail || "Cannot reach the API.";
    }
    if (err.status === 401) {
      return err.detail || "Invalid email or password.";
    }
    if (err.status >= 500) {
      return err.detail || "Service temporarily unavailable.";
    }
    return err.detail || err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
