import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" so frontend/dist/index.html works when PyWebView serves it from any folder.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    port: 5173,
    // the canonical client lives in ../docs/codex and the key labels in ../data
    fs: { allow: [".."] },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 1200,
  },
});
