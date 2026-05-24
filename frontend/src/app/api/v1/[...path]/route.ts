import { NextRequest, NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/api-config";

const SKIP_HEADERS = [
  "host",
  "connection",
  "content-length",
  "transfer-encoding",
];

async function proxy(request: NextRequest, segments: string[]) {
  const targetUrl = `${getBackendUrl()}/api/v1/${segments.join("/")}${request.nextUrl.search}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!SKIP_HEADERS.includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  try {
    const upstream = await fetch(targetUrl, init);
    const outHeaders = new Headers();
    const contentType = upstream.headers.get("content-type");
    if (contentType) outHeaders.set("content-type", contentType);

    return new NextResponse(await upstream.arrayBuffer(), {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: outHeaders,
    });
  } catch (err) {
    console.error("API proxy failed", { targetUrl, err });
    return NextResponse.json({ detail: "Backend service unavailable" }, { status: 502 });
  }
}

type Ctx = { params: Promise<{ path: string[] }> };

async function handle(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  return proxy(request, path);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
