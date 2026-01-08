/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
    optimizeCss: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  // Enable static optimization for better performance
  output: 'standalone',
  
  // Compress responses
  compress: true,
  
  // Generate ETags for better caching
  generateEtags: true,
  
  // Turbopack configuration (Next.js 16+)
  turbopack: {},
};

module.exports = nextConfig;