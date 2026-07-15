import type { NextConfig } from "next";
const backendUrl=(process.env.BACKEND_INTERNAL_URL||"http://backend:8000").replace(/\/$/,"");
const config:NextConfig={output:"standalone",async rewrites(){return [{source:"/api/:path*",destination:`${backendUrl}/api/:path*`}];}};
export default config;
