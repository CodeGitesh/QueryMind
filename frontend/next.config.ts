import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",  // for Docker multi-stage build
  reactStrictMode: true,
  
  // API proxy to backend (avoids CORS issues in dev)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
