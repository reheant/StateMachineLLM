import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Pin Turbopack's root to this directory so it never mistakes a parent
  // directory (e.g. a stray package-lock.json one level up) for the workspace
  // root, which would cause tailwindcss resolution failures and scan the
  // entire .venv/ tree into the file watcher.
  turbopack: {
    root: __dirname,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
