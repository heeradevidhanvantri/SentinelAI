// Browser hits same-origin /api/v1/* (proxied in app/api/v1/[...path]/route.ts).
const PRODUCTION_API_URL = "https://sentinelai-lee4.onrender.com";
const LOCAL_API_URL = "http://localhost:8000";

export function getBackendUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured) return configured;
  return process.env.NODE_ENV === "production" ? PRODUCTION_API_URL : LOCAL_API_URL;
}

export function buildApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (typeof window !== "undefined") return normalized;
  return `${getBackendUrl()}${normalized}`;
}
