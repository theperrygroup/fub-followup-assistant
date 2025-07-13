/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverComponentsExternalPackages: ['stripe']
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
    STRIPE_PUBLISHABLE_KEY: process.env.STRIPE_PUBLISHABLE_KEY,
    API_BASE_URL: process.env.API_BASE_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_BASE_URL || 'http://localhost:8000'}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig 