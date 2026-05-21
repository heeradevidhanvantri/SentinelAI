/**
 * Resolve API base URL for client and server contexts.
 *
 * In the browser we use same-origin relative URLs so Next.js rewrites
 * proxy requests to the backend (avoids CORS in production).
 * On the server (SSR) we need the full backend URL.
 */
const PRODUCTION_API_URL = "https://sentinelai-lee4.onrender.com";
const LOCAL_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");

  if (typeof window !== "undefined") {
    // Browser: same-origin — proxied via next.config rewrites
    return "";
  }

  return configured || (process.env.NODE_ENV === "production" ? PRODUCTION_API_URL : LOCAL_API_URL);
}

/** Full backend URL used by Next.js rewrites (server/build time). */
export function getBackendUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured) return configured;
  return process.env.NODE_ENV === "production" ? PRODUCTION_API_URL : LOCAL_API_URL;
}

export function buildApiUrl(path: string): string {
  const base = getApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${normalizedPath}` : normalizedPath;
}
