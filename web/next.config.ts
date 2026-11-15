import type { NextConfig } from "next";

// In local development the Python API runs separately (uvicorn on :8000), so proxy /api to it.
// On Vercel the Python function serves /api/* on the same origin, so no rewrite is needed.
const DEV_API = process.env.VERITAS_DEV_API ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [{ source: "/api/:path*", destination: `${DEV_API}/api/:path*` }];
  },
};

export default nextConfig;
