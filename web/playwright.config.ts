import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', browserName: 'chromium', headless: true, viewport: { width: 1366, height: 768 } },
  webServer: [
    { command: 'python -m uvicorn apsla.server.app:app --app-dir ../src --host 127.0.0.1 --port 8010', url: 'http://127.0.0.1:8010/api/health', reuseExistingServer: true, timeout: 120_000 },
    { command: 'npm run dev -- --host 127.0.0.1', url: 'http://127.0.0.1:5173', reuseExistingServer: true, timeout: 120_000 },
  ],
});
