import type { NextConfig } from "next";

// URL interna del backend. El navegador nunca la usa directamente: todas las llamadas van a
// /api/v1 (mismo origen) y Next las reenvía. Así la cookie de sesión es de primer nivel y no hay CORS.
// Puertos propios (3010/8010) para no chocar con otros proyectos que usan 3000/8000.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  devIndicators: false,
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${BACKEND_URL}/api/v1/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
