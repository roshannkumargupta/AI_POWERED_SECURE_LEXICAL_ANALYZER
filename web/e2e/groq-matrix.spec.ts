import { expect, test, type Locator, type Page } from '@playwright/test';

test.describe.serial('H1 Matrix: Real Groq Browser Verification', () => {
  const latencies: Record<string, number> = {};

  async function handleConsent(page: Page) {
    const scrimBtn = page
      .locator('.ide-consent-scrim button, .ide-ai-consent button')
      .filter({ hasText: /Allow/i });
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

  async function ensureConsentGranted(page: Page) {
    await page.goto('/');
    const badge = page.locator('.ide-ai-provider-badge');
    await expect(badge).toBeVisible({ timeout: 15_000 });
    await expect(badge).toContainText('groq');

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
  }

  async function setEditorCode(page: Page, language: string, code: string) {
    await page.goto('/');
    await handleConsent(page);

    // Set language
    const langBtn = page.locator('.ide-language-wrap button').first();
    await expect(langBtn).toBeVisible({ timeout: 10_000 });
    const currentText = await langBtn.innerText().catch(() => '');
    if (!currentText.toLowerCase().includes(language.toLowerCase())) {
      await langBtn.click();
      const langOption = page
        .locator('.ide-language-menu button')
        .filter({ hasText: language })
        .first();
      await expect(langOption).toBeVisible({ timeout: 5000 });
      await langOption.click();
      await page.waitForTimeout(500);
    }

    const editorInput = page.locator('.monaco-editor textarea').first();
    await editorInput.focus();
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(code);
    await page.waitForTimeout(500);

    const analyzeBtn = page.getByRole('button', { name: 'Analyze' }).first();
    await analyzeBtn.click();
    await page.waitForTimeout(2500);
  }

  async function waitForCandidate(page: Page, drawer: Locator, tabName: string) {
    const candidateTab = page.locator('.ide-tab', { hasText: tabName });
    const retryBtn = drawer.getByRole('button', { name: /Retry/ });

    for (let i = 0; i < 40; i++) {
      if (await candidateTab.isVisible().catch(() => false)) {
        return;
      }
      if (await retryBtn.isVisible().catch(() => false)) {
        await handleConsent(page);
        await retryBtn.click();
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1000);
    }
    await expect(candidateTab).toBeVisible({ timeout: 20_000 });
  }

  async function waitForExplain(page: Page) {
    const output = page.locator('.ide-ai-output').first();
    const retryBtn = page.getByRole('button', { name: /Retry/ });

    for (let i = 0; i < 35; i++) {
      if (await output.isVisible().catch(() => false)) {
        return;
      }
      if (await retryBtn.isVisible().catch(() => false)) {
        await handleConsent(page);
        await retryBtn.click();
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1000);
    }
    await expect(output).toBeVisible({ timeout: 20_000 });
  }

  async function waitForDiff(page: Page, modal: Locator) {
    const diff = modal.locator('.ide-fix-diff');
    const retryBtn = modal.getByRole('button', { name: /Retry/ });

    for (let i = 0; i < 35; i++) {
      await handleConsent(page);
      if (await diff.isVisible().catch(() => false)) {
        return;
      }
      if (await retryBtn.isVisible().catch(() => false)) {
        await handleConsent(page);
        await retryBtn.click();
        await page.waitForTimeout(2000);
      }
      await page.waitForTimeout(1000);
    }
    await expect(diff).toBeVisible({ timeout: 20_000 });
  }

  test.beforeEach(async ({ page }) => {
    test.setTimeout(120_000);
    await page.waitForTimeout(2000);
  });

  test.afterAll(() => {
    console.log('\n================ REAL GROQ LATENCY REPORT ================');
    for (const [key, ms] of Object.entries(latencies)) {
      console.log(`  ${key.padEnd(36)}: ${ms.toFixed(0)} ms (${(ms / 1000).toFixed(2)} s)`);
    }
    console.log('==========================================================\n');
  });

  test('0. Setup remote consent and verify Groq provider badge', async ({ page }) => {
    await ensureConsentGranted(page);
  });

  // 1. BUILD WITH AI (4 Languages)
  test('1a. Build with AI: Python', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('python');
    await page
      .getByPlaceholder('Describe the code candidate you need')
      .fill('def fibonacci(n: int) -> list[int]: return first n fibonacci numbers');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidate(page, drawer, 'AI candidate.py');
    latencies['Build with AI (Python)'] = Date.now() - t0;
    await expect(page.locator('.monaco-editor')).toContainText('fibonacci');
  });

  test('1b. Build with AI: Java', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('java');
    await page
      .getByPlaceholder('Describe the code candidate you need')
      .fill('public class MathUtils { public static int square(int x) { return x * x; } }');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidate(page, drawer, 'AI candidate.java');
    latencies['Build with AI (Java)'] = Date.now() - t0;
    await expect(page.locator('.monaco-editor')).toContainText('MathUtils');
  });

  test('1c. Build with AI: JavaScript', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('javascript');
    await page
      .getByPlaceholder('Describe the code candidate you need')
      .fill('function add(a, b) { return a + b; }');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidate(page, drawer, 'AI candidate.js');
    latencies['Build with AI (JavaScript)'] = Date.now() - t0;
    await expect(page.locator('.monaco-editor')).toContainText('add');
  });

  test('1d. Build with AI: C++', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Build with AI' }).first().click();
    const drawer = page.getByRole('dialog', { name: 'Build with AI' });
    await expect(drawer).toBeVisible();

    await drawer.locator('select').selectOption('cpp');
    await page
      .getByPlaceholder('Describe the code candidate you need')
      .fill('int multiply(int a, int b) { return a * b; }');

    const t0 = Date.now();
    await page.getByRole('button', { name: 'Generate' }).click();
    await handleConsent(page);

    await waitForCandidate(page, drawer, 'AI candidate.cpp');
    latencies['Build with AI (C++)'] = Date.now() - t0;
    await expect(page.locator('.monaco-editor')).toContainText('multiply');
  });

  // 2. AI EXPLAIN (4 Languages)
  test('2a. AI Explain: Python', async ({ page }) => {
    await setEditorCode(page, 'Python', 'import os\nos.system(input())\n');
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainBtn = page.getByRole('button', { name: /Explain.*file/i });
    await expect(explainBtn).toBeEnabled({ timeout: 10_000 });

    const t0 = Date.now();
    await explainBtn.click();
    await handleConsent(page);
    await waitForExplain(page);
    latencies['AI Explain (Python)'] = Date.now() - t0;
  });

  test('2b. AI Explain: Java', async ({ page }) => {
    await setEditorCode(
      page,
      'Java',
      'import java.sql.*;\nclass Sql {\n  void run(String input, Statement st) throws Exception {\n    st.executeQuery("SELECT * FROM users WHERE name = \'" + input + "\'");\n  }\n}\n'
    );
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainBtn = page.getByRole('button', { name: /Explain.*file/i });
    await expect(explainBtn).toBeEnabled({ timeout: 10_000 });

    const t0 = Date.now();
    await explainBtn.click();
    await handleConsent(page);
    await waitForExplain(page);
    latencies['AI Explain (Java)'] = Date.now() - t0;
  });

  test('2c. AI Explain: JavaScript', async ({ page }) => {
    await setEditorCode(
      page,
      'JavaScript',
      'const express = require("express");\nconst app = express();\napp.get("/run", (req, res) => {\n  eval(req.query.cmd);\n});\n'
    );
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainBtn = page.getByRole('button', { name: /Explain.*file/i });
    await expect(explainBtn).toBeEnabled({ timeout: 10_000 });

    const t0 = Date.now();
    await explainBtn.click();
    await handleConsent(page);
    await waitForExplain(page);
    latencies['AI Explain (JavaScript)'] = Date.now() - t0;
  });

  test('2d. AI Explain: C++', async ({ page }) => {
    await setEditorCode(
      page,
      'C++',
      'void run(char *input) {\n  char buf[8];\n  strcpy(buf, input);\n}\n'
    );
    await page.getByRole('tab', { name: 'AI Explain' }).click();
    const explainBtn = page.getByRole('button', { name: /Explain.*file/i });
    await expect(explainBtn).toBeEnabled({ timeout: 10_000 });

    const t0 = Date.now();
    await explainBtn.click();
    await handleConsent(page);
    await waitForExplain(page);
    latencies['AI Explain (C++)'] = Date.now() - t0;
  });

  // 3. FIX WITH AI (4 Languages)
  async function runFixWithAI(page: Page, language: string, code: string, label: string) {
    await setEditorCode(page, language, code);
    const fixWithAiBtn = page.getByRole('button', { name: 'Fix with AI' }).first();
    await expect(fixWithAiBtn).toBeEnabled({ timeout: 10_000 });
    await fixWithAiBtn.click();
    await page.waitForTimeout(1000);
    await handleConsent(page);

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    const t0 = Date.now();
    await handleConsent(page);

    const allowAndPropose = modal.getByRole('button', { name: /Allow and propose/i });
    if (await allowAndPropose.isVisible({ timeout: 1500 }).catch(() => false)) {
      await allowAndPropose.click();
    } else {
      const improveBtn = modal.getByRole('button', { name: /Improve with AI/ });
      if (await improveBtn.isVisible({ timeout: 2500 }).catch(() => false)) {
        await improveBtn.click();
        await page.waitForTimeout(500);
        await handleConsent(page);
      }
    }
    await waitForDiff(page, modal);
    latencies[`Fix with AI (${label})`] = Date.now() - t0;

    const applyBtn = page.getByRole('button', { name: 'Apply' });
    await expect(applyBtn).toBeEnabled({ timeout: 10_000 });
    await applyBtn.click();
    await page.waitForTimeout(1000);
  }

  test('3a. Fix with AI: Python', async ({ page }) => {
    await runFixWithAI(page, 'Python', 'import os\nos.system("ping " + host)\n', 'Python');
  });

  test('3b. Fix with AI: Java', async ({ page }) => {
    await runFixWithAI(
      page,
      'Java',
      'class X {\n  void f(String host) throws Exception {\n    Runtime.getRuntime().exec("ping " + host);\n  }\n}\n',
      'Java'
    );
  });

  test('3c. Fix with AI: JavaScript', async ({ page }) => {
    await runFixWithAI(page, 'JavaScript', 'eval(cmd);\n', 'JavaScript');
  });

  test('3d. Fix with AI: C++', async ({ page }) => {
    await runFixWithAI(
      page,
      'C++',
      'void f(char* src) {\n  char buf[8];\n  strcpy(buf, src);\n}\n',
      'C++'
    );
  });

  // 4. SAFETY LAB LIVE (4 Languages)
  async function runSafetyLabLive(page: Page, lang: string, label: string) {
    await page.goto('/');
    await handleConsent(page);

    const safetyView = page.locator('.ide-safety-columns');
    if (!(await safetyView.isVisible().catch(() => false))) {
      const safetyLabBtn = page.getByRole('button', { name: 'Agent Safety Lab' }).first();
      await expect(safetyLabBtn).toBeVisible({ timeout: 10_000 });
      await safetyLabBtn.click();
    }
    await expect(safetyView).toBeVisible({ timeout: 15_000 });

    const scenarioCard = page
      .locator('.ide-scenario-card')
      .filter({ hasText: /Safe input resembling an attack/i })
      .first();
    await expect(scenarioCard).toBeVisible({ timeout: 25_000 });
    await scenarioCard.click();

    // Select language
    const langSelect = page.locator('.ide-safety-column label select').first();
    await expect(langSelect).toBeVisible({ timeout: 5000 });
    await langSelect.selectOption(lang);

    // Select LIVE mode
    const modeSelect = page.locator('.ide-safety-column label select').nth(1);
    await expect(modeSelect).toBeVisible({ timeout: 5000 });
    await modeSelect.selectOption('LIVE');

    const t0 = Date.now();
    const runBtn = page.locator('button.ide-safety-run');
    await expect(runBtn).toBeEnabled({ timeout: 10_000 });
    await runBtn.click();
    await handleConsent(page);

    const resultView = page.locator('.ide-safety-result').first();
    await expect(resultView).toBeVisible({ timeout: 60_000 });
    latencies[`Safety Lab Live (${label})`] = Date.now() - t0;

    const outcome = page.locator('.ide-safety-outcome');
    await expect(outcome).toBeVisible();
    await expect(outcome).toContainText(/Attack resisted|pass/i);

    await page.keyboard.press('Escape');
  }

  test('4a. Safety Lab Live: Python', async ({ page }) => {
    await runSafetyLabLive(page, 'python', 'Python');
  });

  test('4b. Safety Lab Live: Java', async ({ page }) => {
    await runSafetyLabLive(page, 'java', 'Java');
  });

  test('4c. Safety Lab Live: JavaScript', async ({ page }) => {
    await runSafetyLabLive(page, 'javascript', 'JavaScript');
  });

  test('4d. Safety Lab Live: C++', async ({ page }) => {
    await runSafetyLabLive(page, 'cpp', 'C++');
  });
});
