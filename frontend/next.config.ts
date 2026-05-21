import type { NextConfig } from "next";

const PRODUCTION_API_URL = "https://sentinelai-lee4.onrender.com";
const LOCAL_API_URL = "http://localhost:8000";

const backendUrl = (
  process.env.NEXT_PUBLIC_API_URL || (
    process.env.NODE_ENV === "production" ? PRODUCTION_API_URL : LOCAL_API_URL
  )
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
