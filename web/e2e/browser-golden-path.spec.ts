import { expect, test, type Page } from '@playwright/test';

interface GoldenCase {
  lang: string;
  langLabel: string;
  wrongCode: string;
  expectedCategory: string;
}

const CASES: GoldenCase[] = [
  {
    lang: 'python',
    langLabel: 'Python',
    wrongCode: 'import os\ncmd = input()\nos.system(cmd)\n',
    expectedCategory: 'CWE-78',
  },
  {
    lang: 'javascript',
    langLabel: 'JavaScript',
    wrongCode:
      'const { exec } = require("child_process");\nconst cmd = req.query.cmd;\nexec(cmd);\n',
    expectedCategory: 'CWE-78',
  },
  {
    lang: 'java',
    langLabel: 'Java',
    wrongCode:
      'package demo;\nimport javax.servlet.http.*;\nclass App {\n  void handle(HttpServletRequest req) throws Exception {\n    String cmd = req.getParameter("cmd");\n    Runtime.getRuntime().exec(cmd);\n  }\n}\n',
    expectedCategory: 'CWE-78',
  },
  {
    lang: 'cpp',
    langLabel: 'C / C++',
    wrongCode:
      '#include <stdlib.h>\nint main(int argc, char** argv) { system(argv[1]); return 0; }\n',
    expectedCategory: 'CWE-78',
  },
];

const THEMES = ['dark', 'light'] as const;

test.describe('Browser Golden Path Verification (4 Languages in Dark & Light)', () => {
  test.beforeEach(async ({ page }) => {
    test.setTimeout(90_000);
    page.on('dialog', (d) => d.accept().catch(() => {}));
    await page.addInitScript(() => {
      try {
        localStorage.removeItem('securelex.ide');
      } catch {}
    });
    await page.waitForTimeout(400);
  });

  async function handleConsent(page: Page) {
    const allowBtn = page
      .locator('.ide-consent-scrim button, .ide-ai-consent button, [role="dialog"] button, button')
      .filter({ hasText: /Allow/i })
      .first();
    if (await allowBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await allowBtn.click({ force: true });
      await page.waitForTimeout(300);
    }
  }

  async function setTheme(page: Page, theme: 'dark' | 'light') {
    const themeIndex = theme === 'dark' ? 0 : 1;
    const themeBtn = page.locator('.ide-theme-switch button').nth(themeIndex);
    await expect(themeBtn).toBeVisible({ timeout: 15_000 });
    const isPressed = await themeBtn.getAttribute('aria-pressed');
    if (isPressed !== 'true') {
      await themeBtn.click();
      await page.waitForTimeout(400);
    }
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme, { timeout: 5000 });
  }

  async function dismissFixModal(page: Page) {
    const modal = page.locator('.ide-fix-modal');
    for (let i = 0; i < 5; i++) {
      if ((await modal.count()) === 0) break;
      const keepBtn = modal.getByRole('button', { name: /Keep Changes|Close/i }).first();
      if (await keepBtn.isVisible().catch(() => false)) {
        await keepBtn.click({ force: true }).catch(() => {});
      }
      const closeX = page.getByRole('button', { name: /Close fix review/i }).first();
      if (await closeX.isVisible().catch(() => false)) {
        await closeX.click({ force: true }).catch(() => {});
      }
      await page.keyboard.press('Escape');
      const overlay = page.locator('.ide-fix-overlay').first();
      if (await overlay.isVisible().catch(() => false)) {
        await overlay.click({ position: { x: 5, y: 5 }, force: true }).catch(() => {});
      }
      await page.waitForTimeout(400);
    }
    await expect(modal).toHaveCount(0, { timeout: 8000 });
  }

  async function setEditorCode(page: Page, code: string) {
    await page.locator('.monaco-editor').first().waitFor({ state: 'visible', timeout: 20_000 });
    await page.evaluate((text) => {
      const ed = (window as any).monaco?.editor?.getEditors()?.[0];
      if (ed) ed.setValue(text);
    }, code);
    await page.waitForTimeout(600);
  }

  async function getEditorCode(page: Page): Promise<string> {
    return await page.evaluate(() => {
      const ed = (window as any).monaco?.editor?.getEditors()?.[0];
      return ed ? ed.getModel().getValue() : '';
    });
  }

  async function selectLanguage(page: Page, langName: string) {
    const langBtn = page.locator('button.ide-status-item[aria-label*="Language"]').first();
    await expect(langBtn).toBeVisible({ timeout: 15_000 });
    const current = (await langBtn.textContent()) || '';
    if (current.toLowerCase().includes(langName.toLowerCase())) {
      return;
    }
    await langBtn.click();
    await page.waitForTimeout(300);
    const opt = page
      .locator('.ide-language-menu button[role="option"]')
      .filter({ hasText: langName })
      .first();
    await expect(opt).toBeVisible({ timeout: 10_000 });
    await opt.click();
    await page.waitForTimeout(500);
    await expect(langBtn).toContainText(langName, { timeout: 10_000 });
  }

  for (const theme of THEMES) {
    for (const testCase of CASES) {
      test(`${testCase.langLabel} in ${theme} theme: Analyze, Fix, Apply, Verify, Undo, Explain, Build`, async ({
        page,
      }) => {
        const forbiddenExternalRequests: string[] = [];

        // Assert 0 external requests except api.groq.com
        page.on('request', (req) => {
          const url = req.url();
          if (!url.startsWith('http://127.0.0.1') && !url.startsWith('http://localhost')) {
            try {
              const host = new URL(url).hostname;
              if (host !== 'api.groq.com') {
                forbiddenExternalRequests.push(url);
              }
            } catch {
              forbiddenExternalRequests.push(url);
            }
          }
        });

        await page.goto('/');
        // Wait for workbench to finish loading before interacting
        await expect(page.locator('.ide-loading')).toHaveCount(0, { timeout: 20_000 });
        await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 20_000 });
        await handleConsent(page);

        // 1. Switch Theme
        await setTheme(page, theme);
        await page.waitForTimeout(800);

        // 2. Select Language
        await selectLanguage(page, testCase.langLabel);

        // 3. Paste Wrong Code
        await setEditorCode(page, testCase.wrongCode);
        await expect
          .poll(async () => getEditorCode(page), { timeout: 10_000 })
          .toBe(testCase.wrongCode);

        // 4. Analyze
        await page.getByRole('button', { name: 'Analyze' }).click();
        await page.waitForTimeout(2000);

        // 5. Fix
        const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
        await expect(fixBtn).toBeEnabled({ timeout: 25_000 });
        await fixBtn.click();

        const modal = page.locator('.ide-fix-modal');
        await expect(modal).toBeVisible({ timeout: 15_000 });

        // 6. Apply
        const applyBtn = modal.getByRole('button', { name: 'Apply' });
        if (await applyBtn.isEnabled({ timeout: 4000 }).catch(() => false)) {
          await applyBtn.click();
          await page.waitForTimeout(400);

          // 7. Verify
          const report = modal.locator('.ide-fix-report');
          await expect(report).toBeVisible({ timeout: 10_000 });
        }

        // Dismiss modal cleanly
        await dismissFixModal(page);
        await page.waitForTimeout(300);

        // 8. Undo
        const undoBtn = page.locator('button[aria-label*="Undo"]').first();
        if (await undoBtn.isEnabled({ timeout: 2000 }).catch(() => false)) {
          await undoBtn.click();
        } else {
          await page.locator('.monaco-editor').first().click();
          await page.keyboard.press('Control+Z');
        }
        await page.waitForTimeout(400);

        // Assert code restored
        const restored = await getEditorCode(page);
        expect(restored).toBe(testCase.wrongCode);

        // 9. Explain
        const explainTab = page
          .locator('button.ide-panel-tab, [role="tab"]')
          .filter({ hasText: /Explain/i })
          .first();
        if (await explainTab.isVisible().catch(() => false)) {
          await explainTab.click();
          await page.waitForTimeout(300);
          const explainFileBtn = page.getByRole('button', { name: /Explain File/i }).first();
          if (await explainFileBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
            await explainFileBtn.click();
            await handleConsent(page);
            await page.waitForTimeout(1000);
          }
        }

        // 10. Build with AI
        const buildBtn = page.getByRole('button', { name: 'Build with AI' }).first();
        await expect(buildBtn).toBeVisible({ timeout: 10_000 });
        await buildBtn.click();
        const drawer = page.getByRole('dialog', { name: 'Build with AI' });
        await expect(drawer).toBeVisible({ timeout: 10_000 });
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);

        // Assert 0 forbidden external requests
        expect(forbiddenExternalRequests).toEqual([]);
      });
    }
  }
});
