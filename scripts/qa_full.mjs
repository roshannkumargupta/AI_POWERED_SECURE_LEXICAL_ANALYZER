#!/usr/bin/env node
/**
 * scripts/qa_full.mjs
 * Full QA Pipeline:
 * 1. Vite build (type check + bundle + test harness exclusion check)
 * 2. Vitest unit and guard tests
 * 3. Python ruff linter check
 * 4. Playwright browser verification
 */

import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');
const WEB_DIR = path.resolve(ROOT, 'web');

function runStep(name, cmd, cwd) {
  console.log(`\n========================================`);
  console.log(`[QA:FULL] STEP: ${name}`);
  console.log(`Command: ${cmd}`);
  console.log(`========================================\n`);
  try {
    execSync(cmd, { cwd, stdio: 'inherit' });
    console.log(`\n>>> [QA:FULL] ${name}: PASS\n`);
  } catch (err) {
    console.error(`\n>>> [QA:FULL] ${name}: FAIL (exit code ${err.status})\n`);
    process.exit(1);
  }
}

console.log('=== Starting SecureLex IDE UI-9 QA Full Pipeline ===');

// 1. Build
runStep('Frontend Production Build', 'npm.cmd run build', WEB_DIR);

// 2. Vitest
runStep('Frontend Vitest Suite & UI-9 Guards', 'npm.cmd test', WEB_DIR);

// 3. Ruff
runStep('Backend Python Ruff Check', '.\\.venv\\Scripts\\ruff.exe check .', ROOT);

// 4. Matrix & browser E2E
runStep('Playwright Browser E2E', 'npm.cmd run e2e', WEB_DIR);

console.log('\n========================================');
console.log('=== [QA:FULL] ALL SUITES PASSED (100% PASS) ===');
console.log('========================================\n');
process.exit(0);
