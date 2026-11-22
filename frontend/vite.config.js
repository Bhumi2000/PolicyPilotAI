import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the frontend calls /api/* on the Vite dev server and Vite
// proxies those calls to the FastAPI backend on port 8000. This keeps the API
// key and backend off the client entirely.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
