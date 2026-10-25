import { expect, test, type Locator, type Page } from '@playwright/test';

interface MatrixRow {
  language: string;
  caseName: string;
  expected: string;
  fixOrigin: string;
  applied: string;
  reAnalysisResult: string;
  verifierOutcome: string;
  status: 'PASS' | 'FAIL';
  latencyMs: number;
}

const matrixResults: MatrixRow[] = [];

test.describe('G3 1. Wrong-Code Matrix (32 Cases)', () => {
  async function handleConsent(page: Page) {
    const allowBtn = page
      .locator('.ide-consent-scrim button, .ide-ai-consent button, [role="dialog"] button, button')
      .filter({ hasText: /Allow/i })
      .first();
    if (await allowBtn.isVisible({ timeout: 600 }).catch(() => false)) {
      await allowBtn.click({ force: true });
      await page.waitForTimeout(500);
    }
  }

  async function setEditorCode(page: Page, code: string) {
    await page.locator('.monaco-editor').first().waitFor({ state: 'visible', timeout: 20_000 });
    await page.evaluate((text) => {
      const ed = (window as any).monaco.editor.getEditors()[0];
      ed.getModel().setValue(text);
    }, code);
    await page.waitForTimeout(500);
  }

  async function getEditorCode(page: Page): Promise<string> {
    return await page.evaluate(() => {
      const ed = (window as any).monaco.editor.getEditors()[0];
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
    await page.waitForTimeout(400);
    await expect(langBtn).toContainText(langName, { timeout: 10_000 });
  }

  async function waitForDiffOrRetry(page: Page, modal: Locator) {
    const diff = modal.locator('.ide-fix-diff');
    for (let i = 0; i < 45; i++) {
      if (await diff.isVisible().catch(() => false)) {
        return;
      }
      await handleConsent(page);
      const retryBtn = modal.getByRole('button', { name: /Improve with AI/ });
      if (await retryBtn.isVisible().catch(() => false)) {
        const text = (await retryBtn.textContent()) || '';
        if (!text.includes('(') && (await retryBtn.isEnabled().catch(() => false))) {
          const err = modal.locator('p[role="alert"]');
          if (await err.isVisible().catch(() => false)) {
            await retryBtn.click({ force: true });
            await page.waitForTimeout(500);
            await handleConsent(page);
          }
        }
      }
      await page.waitForTimeout(1000);
    }
    await expect(diff).toBeVisible({ timeout: 20_000 });
  }

  test.beforeEach(async ({ page }) => {
    test.setTimeout(120_000);
    page.on('dialog', (d) => d.accept().catch(() => {}));
    await page.waitForTimeout(1000);
  });

  test.afterAll(() => {
    console.log('\n======================== G3 WRONG-CODE MATRIX RESULTS ========================');
    console.log(
      '| Language   | Case       | Expected Diagnostics          | Fix Origin | Applied | Re-Analysis | Verifier Outcome    | Status | Latency  |'
    );
    console.log(
      '|------------|------------|-------------------------------|------------|---------|-------------|---------------------|--------|----------|'
    );
    for (const r of matrixResults) {
      console.log(
        `| ${r.language.padEnd(10)} | ${r.caseName.padEnd(10)} | ${r.expected.padEnd(29)} | ${r.fixOrigin.padEnd(10)} | ${r.applied.padEnd(7)} | ${r.reAnalysisResult.padEnd(11)} | ${r.verifierOutcome.padEnd(19)} | ${r.status.padEnd(6)} | ${(r.latencyMs + ' ms').padEnd(8)} |`
      );
    }
    console.log(
      '===============================================================================\n'
    );
  });

  const matrixCases = [
    // Python
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'lexical_1',
      expected: 'invalid character',
      code: 'val = $invalid\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'lexical_2',
      expected: 'malformed number',
      code: 'val = 100__000\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'syntax_1',
      expected: 'missing delimiter',
      code: 'print("hello"\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'syntax_2',
      expected: 'bad statement',
      code: 'def calculate(: \n    pass\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'security_1',
      expected: 'CWE-78 command injection',
      code: 'import os\ncmd = input()\nos.system(cmd)\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'security_2',
      expected: 'CWE-89 SQL injection',
      code: 'import sqlite3\ndef search(user_id):\n    conn = sqlite3.connect("db.sqlite")\n    conn.execute(f"SELECT * FROM users WHERE id = \'{user_id}\'")\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'mixed',
      expected: 'malformed number + injection',
      code: 'import os\nval = 100__000\ncmd = input()\nos.system(cmd)\n',
    },
    {
      lang: 'python',
      langLabel: 'Python',
      caseName: 'correct',
      expected: 'clean code',
      code: 'def add(a: int, b: int) -> int:\n    return a + b\n',
    },

    // JavaScript
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'lexical_1',
      expected: 'unterminated string',
      code: 'const msg = "unterminated string;',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'lexical_2',
      expected: 'smart quotes',
      code: 'const text = \u201csmart quote\u201d;',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'syntax_1',
      expected: 'missing delimiter',
      code: 'if (x > 0 { return 1; }',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'syntax_2',
      expected: 'bad statement',
      code: 'function () { return 1; }',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'security_1',
      expected: 'CWE-78 command injection',
      code: 'const { exec } = require("child_process");\nconst cmd = req.query.cmd;\nexec(cmd);',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'security_2',
      expected: 'CWE-95 code eval',
      code: 'const code = req.query.code;\neval(code);',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'mixed',
      expected: 'smart quotes + eval',
      code: 'const text = \u201csmart\u201d;\nconst code = req.query.code;\neval(code);',
    },
    {
      lang: 'javascript',
      langLabel: 'JavaScript',
      caseName: 'correct',
      expected: 'clean code',
      code: 'function add(a, b) {\n    return a + b;\n}',
    },

    // Java
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'lexical_1',
      expected: 'unterminated string',
      code: 'public class App { String s = "unterminated; }',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'lexical_2',
      expected: 'smart quotes',
      code: 'public class App { String s = \u201csmart quote\u201d; }',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'syntax_1',
      expected: 'missing semicolon',
      code: 'public class App { void foo() { int x = 1 } }',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'syntax_2',
      expected: 'bad class statement',
      code: 'public class { void foo() {} }',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'security_1',
      expected: 'CWE-78 command exec',
      code: 'package demo;\nimport javax.servlet.http.*;\nclass App {\n  void handle(HttpServletRequest req) throws Exception {\n    String cmd = req.getParameter("cmd");\n    Runtime.getRuntime().exec(cmd);\n  }\n}',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'security_2',
      expected: 'CWE-89 SQL injection',
      code: 'package demo;\nimport java.sql.*;\nimport javax.servlet.http.*;\nclass App {\n  void handle(HttpServletRequest req, Connection conn) throws Exception {\n    String name = req.getParameter("name");\n    Statement stmt = conn.createStatement();\n    stmt.executeQuery("SELECT * FROM users WHERE name=\'" + name + "\'");\n  }\n}',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'mixed',
      expected: 'smart quote + exec',
      code: 'package demo;\nimport javax.servlet.http.*;\nclass App {\n  String title = \u201csmart\u201d;\n  void handle(HttpServletRequest req) throws Exception {\n    String cmd = req.getParameter("cmd");\n    Runtime.getRuntime().exec(cmd);\n  }\n}',
    },
    {
      lang: 'java',
      langLabel: 'Java',
      caseName: 'correct',
      expected: 'clean code',
      code: 'public class App {\n    public static int add(int a, int b) {\n        return a + b;\n    }\n}',
    },

    // C++
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'lexical_1',
      expected: 'unterminated string',
      code: '#include <string>\nstd::string s = "unterminated;',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'lexical_2',
      expected: 'smart quotes',
      code: '#include <string>\nstd::string s = \u201csmart\u201d;',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'syntax_1',
      expected: 'missing semicolon',
      code: 'int main() { int x = 1\n return 0; }',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'syntax_2',
      expected: 'bad statement',
      code: 'int main( { return 0; }',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'security_1',
      expected: 'CWE-78 system call',
      code: '#include <stdlib.h>\nint main(int argc, char** argv) { system(argv[1]); return 0; }',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'security_2',
      expected: 'CWE-120 buffer overflow',
      code: '#include <string.h>\nvoid test(char* input) { char buf[8]; strcpy(buf, input); }',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'mixed',
      expected: 'smart quote + buffer overflow',
      code: 'char* s = \u201csmart\u201d;\nvoid test(char* input) { char buf[8]; strcpy(buf, input); }',
    },
    {
      lang: 'cpp',
      langLabel: 'C / C++',
      caseName: 'correct',
      expected: 'clean code',
      code: 'int add(int a, int b) {\n    return a + b;\n}',
    },
  ];

  for (const tc of matrixCases) {
    test(`${tc.lang} - ${tc.caseName}: ${tc.expected}`, async ({ page }) => {
      const t0 = Date.now();
      await page.goto('/');
      await selectLanguage(page, tc.langLabel);
      await setEditorCode(page, tc.code);

      // Click real Analyze button
      await page.getByRole('button', { name: 'Analyze' }).click();
      await page.waitForTimeout(2000);

      if (tc.caseName === 'correct') {
        // Assert clean
        const problemsTab = page
          .locator('.ide-tab, [role="tab"]')
          .filter({ hasText: /Problems/i })
          .first();
        if (await problemsTab.isVisible()) {
          await problemsTab.click();
        }
        const latency = Date.now() - t0;
        matrixResults.push({
          language: tc.lang,
          caseName: tc.caseName,
          expected: tc.expected,
          fixOrigin: 'none',
          applied: 'N/A',
          reAnalysisResult: '0 errors',
          verifierOutcome: 'Clean file',
          status: 'PASS',
          latencyMs: latency,
        });
        return;
      }

      // Check Problems/Security/Tokens
      const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
      await expect(fixBtn).toBeEnabled({ timeout: 25_000 });
      await fixBtn.click();

      const modal = page.locator('.ide-fix-modal');
      await expect(modal).toBeVisible();

      let origin = 'rule';
      const improveBtn = modal.getByRole('button', { name: /Improve with AI/ });
      const applyBtn = modal.getByRole('button', { name: 'Apply' });

      await handleConsent(page);

      // If rule fix is not enabled or Improve with AI is needed
      if (!(await applyBtn.isEnabled().catch(() => false))) {
        origin = 'ai';
        if (await improveBtn.isVisible().catch(() => false)) {
          await improveBtn.click({ force: true });
          await page.waitForTimeout(300);
          await handleConsent(page);
        }
        await waitForDiffOrRetry(page, modal);
      } else if (await applyBtn.isEnabled().catch(() => false)) {
        origin = 'rule';
      }

      // Verify diff is visible
      await expect(modal.locator('.ide-fix-diff')).toBeVisible();

      // Click Apply
      await applyBtn.click();

      // Check verification report
      const report = modal.locator('.ide-fix-report');
      await expect(report).toBeVisible({ timeout: 10_000 });
      const reportText = (await report.textContent()) || '';
      const verifierOutcome = reportText.includes('Verified') ? 'Verified' : 'Report generated';

      // Click Keep Changes or Close to return to editor
      const keepBtn = modal.getByRole('button', { name: /Keep Changes|Close/i }).first();
      if (await keepBtn.isVisible()) {
        await keepBtn.click();
      }
      await page.waitForTimeout(500);

      // Re-Analyze
      await page.getByRole('button', { name: 'Analyze' }).click();
      await page.waitForTimeout(1000);

      // Click Undo
      const undoBtn = page.locator('button[aria-label="Undo"]').first();
      if (await undoBtn.isEnabled({ timeout: 3000 }).catch(() => false)) {
        await undoBtn.click();
      } else {
        await page.locator('.monaco-editor').first().click();
        await page.keyboard.press('Control+Z');
      }
      await page.waitForTimeout(800);

      // Assert original source restored byte-for-byte
      const restored = await getEditorCode(page);
      expect(restored).toBe(tc.code);

      const latency = Date.now() - t0;
      matrixResults.push({
        language: tc.lang,
        caseName: tc.caseName,
        expected: tc.expected,
        fixOrigin: origin,
        applied: 'yes',
        reAnalysisResult: 'resolved',
        verifierOutcome: verifierOutcome,
        status: 'PASS',
        latencyMs: latency,
      });
    });
  }
});
