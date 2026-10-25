import { defineConfig } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const venvPythonWin = path.resolve(__dirname, '..', '.venv', 'Scripts', 'python.exe');
const venvPythonUnix = path.resolve(__dirname, '..', '.venv', 'bin', 'python');
let pythonCmd = 'python';
if (process.platform === 'win32' && fs.existsSync(venvPythonWin)) {
  pythonCmd = `"${venvPythonWin}"`;
} else if (fs.existsSync(venvPythonUnix)) {
  pythonCmd = `"${venvPythonUnix}"`;
} else if (process.env.VIRTUAL_ENV) {
  pythonCmd = process.platform === 'win32'
    ? `"${path.join(process.env.VIRTUAL_ENV, 'Scripts', 'python.exe')}"`
    : `"${path.join(process.env.VIRTUAL_ENV, 'bin', 'python')}"`;
}

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
    { command: `${pythonCmd} -m uvicorn apsla.server.app:app --app-dir ../src --host 127.0.0.1 --port 8010`, url: 'http://127.0.0.1:8010/api/health', reuseExistingServer: true, timeout: 120_000 },
    { command: 'npm.cmd run dev -- --host 127.0.0.1', url: 'http://127.0.0.1:5173', reuseExistingServer: true, timeout: 120_000 },
  ],
});
