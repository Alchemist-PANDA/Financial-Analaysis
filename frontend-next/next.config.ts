import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: 'standalone', // Standalone is preferred for Docker, but 'export' is causing crashes with dynamic routes.
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
