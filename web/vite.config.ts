/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const apiPort = process.env.APSLA_API_PORT ?? '8000';

function localMonacoLoader() {
  return {
    name: 'securelex-local-monaco-loader',
    enforce: 'pre' as const,
    transform(code: string, id: string) {
      if (!id.includes('@monaco-editor/loader/lib/es/config/index.js')) return null;
      return code.replace('https://cdn.jsdelivr.net/npm/monaco-editor@0.55.1/min/vs', '/monaco/vs');
    },
  };
}

export default defineConfig({
  plugins: [localMonacoLoader(), react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${apiPort}`,
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
  },
});
