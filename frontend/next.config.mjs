/** @type {import('next').NextConfig} */
const nextConfig = {
  // Align with Django/DRF's default trailing slash to avoid redirect loops
  trailingSlash: true,
  async rewrites() {
    const backendOrigin = process.env.BACKEND_ORIGIN || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
