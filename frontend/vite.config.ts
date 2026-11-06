import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true,
      },
    },
  },
  test: {
    // Keep the suite usable on memory-constrained demo laptops.
    maxWorkers: 1,
    minWorkers: 1,
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
