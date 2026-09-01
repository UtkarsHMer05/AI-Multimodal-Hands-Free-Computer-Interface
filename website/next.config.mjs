/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export: the site ships as plain files to Vercel, Netlify, or
  // GitHub Pages with no server runtime. All interactivity (mic, camera,
  // command engine) runs client-side in the visitor's browser.
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
