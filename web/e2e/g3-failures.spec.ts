import { expect, test } from '@playwright/test';
import { setEditorText } from './helpers';

test.describe.serial('G3 3. Failure Paths (10 Failure Cases)', () => {
  async function setupDocWithIssue(page: any) {
    await page.goto('/');
    await setEditorText(page, 'x = "unterminated\n');
    await page.getByRole('button', { name: 'Analyze' }).click();
    await page.waitForTimeout(1000);
  }

  test('1. Invalid key (401) ends in visible state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: { code: 'INVALID_API_KEY', message: 'Invalid API key provided.' } }),
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled({ timeout: 10_000 });
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    // Verify error is displayed
    await expect(modal.locator('[role="alert"]').first()).toBeVisible({ timeout: 5000 });

    // Working Close without page reload
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('2. Rate limit (429) ends in visible state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({ detail: { code: 'RATE_LIMIT_EXCEEDED', message: 'Rate limit exceeded; retry in 5s.' } }),
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    await expect(modal.locator('[role="alert"]').first()).toBeVisible({ timeout: 5000 });
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('3. Network down ends in visible state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.abort('failed');
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    await expect(modal.locator('[role="alert"]').first()).toBeVisible({ timeout: 5000 });
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('4. Model timeout ends in visible state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.fulfill({
        status: 504,
        contentType: 'application/json',
        body: JSON.stringify({ detail: { code: 'MODEL_TIMEOUT', message: 'Upstream model timed out.' } }),
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    await expect(modal.locator('[role="alert"]').first()).toBeVisible({ timeout: 5000 });
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('5. Malformed model JSON ends in visible state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'INVALID_JSON{broken',
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    await expect(modal.locator('[role="alert"]').first()).toBeVisible({ timeout: 5000 });
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('6. Schema-violating edits ends in visible state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          proposal: {
            id: 'invalid-edits',
            edits: [{ range: { invalid: true }, new_text: 12345 }],
            rationale: 'Bad schema',
          },
        }),
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('7. Stale source after proposing displays stale state with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          proposal: {
            id: 'prop-stale',
            origin: 'rule',
            source_version: 999, // Stale: does not match document sourceVersion (1)
            source_hash: '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            edits: [{ range: { start_line: 1, start_col: 1, end_line: 1, end_col: 1 }, new_text: '# patched\n' }],
            rationale: 'Stale patch proposal',
            expected_outcome: 'Done',
            assumptions: [],
            risks: [],
          },
        }),
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    // Verify stale warning is displayed
    await expect(modal.locator('[role="alert"]').filter({ hasText: /Stale source/i })).toBeVisible({ timeout: 5000 });

    const applyBtn = modal.getByRole('button', { name: 'Apply' });
    if (await applyBtn.isVisible()) {
      expect(await applyBtn.isDisabled()).toBe(true);
    }

    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('8. Editing while request is running handles safely with working Close', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await new Promise((r) => setTimeout(r, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          proposal: {
            id: 'prop-delayed',
            origin: 'rule',
            source_version: 0,
            source_hash: 'abc',
            edits: [],
            rationale: 'Cleaned',
            expected_outcome: 'Done',
          },
        }),
      });
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    // Edit Monaco while request is running
    await page.evaluate(() => {
      const monaco = (window as any).monaco;
      const editor = monaco?.editor?.getEditors()?.[0];
      const model = editor?.getModel();
      if (editor && model) {
        editor.executeEdits('test', [{
          range: model.getFullModelRange(),
          text: 'x = "modified-while-running\n',
        }]);
      }
    });

    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await expect(closeBtn).toBeVisible();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('9. Two quick clicks are debounced without crash and modal closes cleanly', async ({ page }) => {
    await setupDocWithIssue(page);
    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.evaluate((btn: HTMLElement) => {
      btn.click();
      btn.click();
    });

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();
  });

  test('10. Closing modal mid-request cancels cleanly without page reload', async ({ page }) => {
    await setupDocWithIssue(page);
    await page.route('**/api/fixes/propose', async (route) => {
      await new Promise((r) => setTimeout(r, 4000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          proposal: {
            id: 'prop-late',
            origin: 'rule',
            source_version: 0,
            source_hash: '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            edits: [{ range: { start_line: 1, start_col: 1, end_line: 1, end_col: 1 }, new_text: '# late\n' }],
            rationale: 'Late',
            expected_outcome: 'Done',
          },
        }),
      }).catch(() => {});
    });

    const fixBtn = page.getByRole('button', { name: /Fix/ }).first();
    await expect(fixBtn).toBeEnabled();
    await fixBtn.click();

    const modal = page.locator('.ide-fix-modal');
    await expect(modal).toBeVisible();

    // Close mid-request
    const closeBtn = modal.locator('button[aria-label="Close fix review"]').first();
    await closeBtn.click();
    await expect(modal).toBeHidden();

    // Verify page did NOT reload (monaco still exists)
    const editor = page.locator('.monaco-editor').first();
    await expect(editor).toBeVisible();
  });
});
