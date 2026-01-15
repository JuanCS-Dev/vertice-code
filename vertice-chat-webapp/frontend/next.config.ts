import type { NextConfig } from 'next';
import withBundleAnalyzer from '@next/bundle-analyzer';

// Bundle analyzer configuration
const bundleAnalyzer = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  // Output standalone for Docker
  output: 'standalone',

  // Enable experimental features
  experimental: {
    // Bundle optimization
    optimizePackageImports: ['@radix-ui/react-icons', 'date-fns'],
  },

  // Optimize imports for better tree shaking
  modularizeImports: {
    'lucide-react': {
      transform: 'lucide-react/dist/esm/icons/{{kebabCase member}}',
    },
    'lodash': {
      transform: 'lodash/{{member}}',
    },
  },

  // Turbopack configuration (empty to avoid webpack conflicts)
  turbopack: {},

  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
      },
      {
        protocol: 'https',
        hostname: 'cdn.vertice.ai',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },

  // Webpack configuration for bundle optimization
  webpack: (config, { isServer }) => {
    // Optimize bundle size and splitting
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // Vendor chunk - third-party libraries
            vendor: {
              name: 'vendor',
              test: /node_modules/,
              priority: 20,
              reuseExistingChunk: true,
            },
            // UI components chunk
            ui: {
              name: 'ui',
              test: /[\\/]components[\\/]ui[\\/]/,
              priority: 15,
              reuseExistingChunk: true,
            },
            // Common chunk - shared between pages
            common: {
              minChunks: 2,
              priority: 10,
              reuseExistingChunk: true,
              enforce: true,
            },
          },
        },
      };
    }

    return config;
  },
};

export default bundleAnalyzer(nextConfig);
