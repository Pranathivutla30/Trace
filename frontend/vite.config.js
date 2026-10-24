import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
// `base` is "/Trace/" for the production build (GitHub Pages serves the site
// under the repo name) and "/" during local dev.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/Trace/" : "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Forward API calls to the FastAPI backend during development.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
}));
