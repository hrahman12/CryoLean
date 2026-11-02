import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // Essential for PyWebView local file loading (file:///.../dist/index.html)
  server: {
    port: 5173,
    strictPort: true,
    fs: { allow: ['..'] },
    proxy: { '/api': process.env.CRYOLEAN_DEV_API ?? 'http://127.0.0.1:8000' },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three/') || id.includes('node_modules/three-stdlib/')) return 'three';
          if (id.includes('node_modules/@react-three/')) return 'react-three';
          if (id.endsWith('/src/data/catalog.json')) return 'catalog';
        },
      },
    },
  },
});
