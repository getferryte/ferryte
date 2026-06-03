/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    FERRYTE_API_BASE: process.env.FERRYTE_API_BASE || "http://127.0.0.1:8787",
  },
};

export default nextConfig;
