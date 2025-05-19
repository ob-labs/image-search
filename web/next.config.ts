import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  /* config options here */
  output: 'export',
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  assetPrefix: process.env.NODE_ENV === 'production' ? '/static' : '',
  env: {
    ASSET_PREFIX: process.env.NODE_ENV === 'production' ? '/static' : '',
  },
  rewrites: async () => {
    return [
      {
        source: '/:path*',
        // 接口 URL
        destination: `http://192.168.1.1:3000/:path*`,
      },
    ]
  },
}

export default nextConfig
