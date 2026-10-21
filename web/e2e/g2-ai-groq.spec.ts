import { expect, test, type Locator, type Page } from '@playwright/test';

test.describe.serial('G2 AI Features with Groq', () => {
  const latencies: Record<string, number> = {};

  async function handleConsent(page: Page) {
    const scrimBtn = page.locator('.ide-consent-scrim button, .ide-ai-consent button').filter({ hasText: /Allow/i });
    if (await scrimBtn.isVisible({ timeout: 800 }).catch(() => false)) {
      await scrimBtn.first().click();
      await page.waitForTimeout(500);
      return;
    }
    const allowBtn = page.getByRole('button', { name: /Allow/i });
    if (await allowBtn.isVisible({ timeout: 800 }).catch(() => false)) {
      await allowBtn.first().click();
      await page.waitForTimeout(500);
    }
  }

  async function waitForCandidateOrRetry(page: Page, drawer: Locator, tabName: string) {
    const candidateTab = page.locator('.ide-tab', { hasText: tabName });
    const retryBtn = drawer.getByRole('button', { name: /Retry/ });

    for (let i = 0; i < 40; i++) {
      if (await candidateTab.isVisible().catch(() => false)) {
        return;
      }
      if (await retryBtn.isVisible().catch(() => false)) {
        const text = (await retryBtn.textContent()) || '';
        if (text.includes('(')) {
          await expect(retryBtn).toHaveText('Retry', { timeout: 20_000 });
        }
        await retryBtn.click();
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1000);
    }
    await expect(candidateTab).toBeVisible({ timeout: 20_000 });
  }

  async function waitForDiffOrRetry(page: Page, modal: Locator) {
    const diff = modal.locator('.ide-fix-diff');
    const retryBtn = modal.getByRole('button', { name: /Retry/ });

    for (let i = 0; i < 35; i++) {
      await handleConsent(page);
      if (await diff.isVisible().catch(() => false)) {
        return;
      }
      if (await retryBtn.isVisible().catch(() => false)) {
        await handleConsent(page);
        const text = (await retryBtn.textContent()) || '';
        if (text.includes('(')) {
          await expect(retryBtn).toHaveText('Retry', { timeout: 20_000 });
        }
        await handleConsent(page);
        await retryBtn.click();
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1000);
    }
    await expect(diff).toBeVisible({ timeout: 20_000 });
  }

  async function waitForExplainOrRetry(page: Page) {
    const output = page.locator('.ide-ai-output').first();
    const retryBtn = page.getByRole('button', { name: /Retry/ });

    for (let i = 0; i < 30; i++) {
      if (await output.isVisible().catch(() => false)) {
        return;
      }
      if (await retryBtn.isVisible().catch(() => false)) {
        const text = (await retryBtn.textContent()) || '';
        if (text.includes('(')) {
          await expect(retryBtn).toHaveText('Retry', { timeout: 20_000 });
        }
        await retryBtn.click();
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1000);
    }
    await expect(output).toBeVisible({ timeout: 20_000 });
  }

  test.beforeEach(async ({ page }) => {
    test.setTimeout(120_000);
    // Pace requests to respect Groq rate limits
    await page.waitForTimeout(4000);
  });

  test.afterAll(() => {
    console.log('\n================ REAL GROQ LATENCY REPORT ================');
    for (const [key, ms] of Object.entries(latencies)) {
      console.log(`  ${key.padEnd(36)}: ${ms.toFixed(0)} ms (${(ms / 1000).toFixed(2)} s)`);
    }
    console.log('==========================================================\n');
  });

  test('0. Setup remote consent and verify Groq provider badge', async ({ page }) => {
    await page.goto('/');
    // Check AI provider badge
    const badge = page.locator('.ide-ai-provider-badge');
    await expect(badge).toBeVisible();
    await expect(badge).toContainText('groq');

    // Grant remote processing consent via Settings
    await page.getByRole('button', { name: 'Settings' }).click();
    const modal = page.getByRole('dialog', { name: 'Workbench Settings' });
    await expect(modal).toBeVisible();
    const consentCheckbox = page.getByLabel(/Allow remote processing/);
    if (await consentCheckbox.isVisible()) {
      const isChecked = await consentCheckbox.isChecked().catch(() => false);
      if (!isChecked) {
        await consentCheckbox.click();
        await page.waitForTimeout(500);
      }
    }
    await page.keyboard.press('Escape');
    await expect(modal).toBeHidden();
  });

  test('1a. Build with AI: Python candidate', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('python');
    await page.getByPlaceholder('Describe the code candidate you need').fill('def fibonacci(n: int) -> list[int]: return first n fibonacci numbers');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidateOrRetry(page, drawer, 'AI candidate.py');
    const elapsed = Date.now() - t0;
    latencies['Build with AI (Python)'] = elapsed;

    await expect(page.locator('.monaco-editor')).toContainText('fibonacci');
  });

  test('1b. Build with AI: Java candidate', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('java');
    await page.getByPlaceholder('Describe the code candidate you need').fill('public class MathUtils { public static int square(int x) { return x * x; } }');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidateOrRetry(page, drawer, 'AI candidate.java');
    const elapsed = Date.now() - t0;
    latencies['Build with AI (Java)'] = elapsed;

    await expect(page.locator('.monaco-editor')).toContainText('MathUtils');
  });

  test('1c. Build with AI: JavaScript candidate', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('javascript');
    await page.getByPlaceholder('Describe the code candidate you need').fill('function add(a, b) { return a + b; }');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidateOrRetry(page, drawer, 'AI candidate.js');
    const elapsed = Date.now() - t0;
    latencies['Build with AI (JavaScript)'] = elapsed;

    await expect(page.locator('.monaco-editor')).toContainText('add');
  });

  test('1d. Build with AI: C++ candidate', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('cpp');
    await page.getByPlaceholder('Describe the code candidate you need').fill('int multiply(int a, int b) { return a * b; }');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidateOrRetry(page, drawer, 'AI candidate.cpp');
    const elapsed = Date.now() - t0;
    latencies['Build with AI (C++)'] = elapsed;

    await expect(page.locator('.monaco-editor')).toContainText('multiply');
  });

  test('2a. Fix with AI: invalid token', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Language/ }).click();
    await page.getByRole('option', { name: 'Python' }).click();

    const editorInput = page.locator('.monaco-editor textarea').first();
    await editorInput.focus();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('x = "unterminated string');
    await page.keyboard.press('End');
    await page.keyboard.press('Backspace');

    await page.getByRole('button', { name: 'Analyze' }).click();

    const fixWithAiBtn = page.getByRole('button', { name: 'Fix with AI' }).first();
    await expect(fixWithAiBtn).toBeEnabled({ timeout: 10_000 });
    await fixWithAiBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    // Improve with AI
    const improveBtn = page.getByRole('button', { name: /Improve with AI/ });
    if (await improveBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      const t0 = Date.now();
      await improveBtn.click();
      await handleConsent(page);
      await waitForDiffOrRetry(page, modal);
      latencies['Fix with AI (Invalid Token)'] = Date.now() - t0;
    } else {
      latencies['Fix with AI (Invalid Token)'] = 0;
    }

    // Apply the fix
    const applyBtn = page.getByRole('button', { name: 'Apply' });
    await expect(applyBtn).toBeEnabled();
    await applyBtn.click();
    await expect(page.locator('.ide-fix-report')).toBeVisible({ timeout: 10_000 });

    // Test Undo
    const undoBtn = page.getByRole('button', { name: 'Undo Changes' });
    await expect(undoBtn).toBeVisible();
    await undoBtn.click();
    await expect(page.locator('.monaco-editor')).toContainText('unterminated string');
  });

  test('2b. Fix with AI: security finding', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Language/ }).click();
    await page.getByRole('option', { name: 'Python' }).click();

    const editorInput = page.locator('.monaco-editor textarea').first();
    await editorInput.focus();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('import os\nos.system(input())\n');

    await page.getByRole('button', { name: 'Analyze' }).click();
    await page.waitForTimeout(1500);

    const fixWithAiBtn = page.getByRole('button', { name: 'Fix with AI' }).first();
    await expect(fixWithAiBtn).toBeEnabled({ timeout: 10_000 });
    await fixWithAiBtn.click();
    await handleConsent(page);

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    const t0 = Date.now();
    await handleConsent(page);

    const improveBtn = modal.getByRole('button', { name: /Improve with AI/ });
    if (await improveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await improveBtn.click();
      await handleConsent(page);
    }

    await waitForDiffOrRetry(page, modal);
    latencies['Fix with AI (Security Finding)'] = Date.now() - t0;

    // Apply the fix and verify
    const applyBtn = page.getByRole('button', { name: 'Apply' });
    await expect(applyBtn).toBeEnabled();
    await applyBtn.click();
    await expect(page.locator('.ide-fix-report')).toBeVisible({ timeout: 10_000 });
    const keepBtn = page.getByRole('button', { name: 'Keep Changes' });
    await expect(keepBtn).toBeVisible();
    await keepBtn.click();
  });

  test('3. Explain: token, problem, finding, and file', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /Language/ }).click();
    await page.getByRole('option', { name: 'Python' }).click();

    const editorInput = page.locator('.monaco-editor textarea').first();
    await editorInput.focus();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('import os\nos.system(input())\n');
    await page.getByRole('button', { name: 'Analyze' }).click();

    // 3a. Explain File
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainFileBtn = page.getByRole('button', { name: /Explain.*file/i });
    await expect(explainFileBtn).toBeEnabled({ timeout: 5000 });
    let t0 = Date.now();
    await explainFileBtn.click();
    await handleConsent(page);
    await waitForExplainOrRetry(page);
    latencies['AI Explain (File)'] = Date.now() - t0;

    await page.waitForTimeout(3000);

    // 3b. Explain Token
    await page.getByRole('tab', { name: 'Tokens' }).click();
    const tokenRow = page.locator('.ide-token-row').first();
    await expect(tokenRow).toBeVisible({ timeout: 5000 });
    await tokenRow.click();
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainTokenBtn = page.getByRole('button', { name: /Explain.*token/i });
    if (await explainTokenBtn.isEnabled()) {
      t0 = Date.now();
      await explainTokenBtn.click();
      await handleConsent(page);
      await waitForExplainOrRetry(page);
      latencies['AI Explain (Token)'] = Date.now() - t0;
    }

    await page.waitForTimeout(3000);

    // 3c. Explain Finding
    await page.getByRole('tab', { name: 'Security' }).click();
    const findingItem = page.locator('.ide-security-row').first();
    await expect(findingItem).toBeVisible({ timeout: 5000 });
    await findingItem.click();
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainFindingBtn = page.getByRole('button', { name: /Explain.*finding/i });
    if (await explainFindingBtn.isEnabled()) {
      t0 = Date.now();
      await explainFindingBtn.click();
      await handleConsent(page);
      await waitForExplainOrRetry(page);
      latencies['AI Explain (Finding)'] = Date.now() - t0;
    }

    await page.waitForTimeout(3000);

    // 3d. Explain Problem
    await editorInput.focus();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('def foo(\n');
    await page.getByRole('button', { name: 'Analyze' }).click();
    await page.getByRole('tab', { name: 'Problems' }).click();
    const problemRow = page.locator('.ide-problem-row').first();
    if (await problemRow.isVisible({ timeout: 5000 }).catch(() => false)) {
      await problemRow.click();
      await page.getByRole('tab', { name: 'AI Explain' }).click();
      const explainProblemBtn = page.getByRole('button', { name: /Explain.*problem/i });
      if (await explainProblemBtn.isEnabled({ timeout: 3000 }).catch(() => false)) {
        t0 = Date.now();
        await explainProblemBtn.click();
        await handleConsent(page);
        await waitForExplainOrRetry(page);
        latencies['AI Explain (Problem)'] = Date.now() - t0;
      }
    }
  });
});
