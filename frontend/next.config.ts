/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/analyze",
        destination: "http://localhost:8000/analyze",
      },
      {
        source: "/api/health",
        destination: "http://localhost:8000/health",
      },
    ];
  },
};

export default nextConfig;
