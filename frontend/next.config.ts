import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the dev server to accept requests proxied from Cloudflare quick
  // tunnels (rotating *.trycloudflare.com hosts) and from the local LAN IP
  // so the demo URL works from any device.
  allowedDevOrigins: [
    "lp-diligence.krawczun.com",
    "*.trycloudflare.com",
    "192.168.1.24",
  ],
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
