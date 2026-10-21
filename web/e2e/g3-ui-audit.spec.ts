import { expect, test } from '@playwright/test';

test.describe.serial('G3 6. UI Click Audit Across Resolutions & Themes', () => {
  const resolutions = [
    { width: 1280, height: 720 },
    { width: 1536, height: 864 },
    { width: 1920, height: 1080 },
  ];

  for (const res of resolutions) {
    for (const theme of ['dark', 'light'] as const) {
      test(`Audit UI at ${res.width}x${res.height} (${theme} mode)`, async ({ page }) => {
        await page.setViewportSize({ width: res.width, height: res.height });
        await page.goto('/');

        // 1. Theme switch button click
        const themeBtn = page.locator(`.ide-theme-switch button`).filter({ hasText: new RegExp(theme, 'i') }).first();
        if (await themeBtn.isVisible()) {
          await themeBtn.click();
          await page.waitForTimeout(200);
        }

        // 2. Settings modal
        const settingsBtn = page.locator('button[aria-label="Settings"]').first();
        await expect(settingsBtn).toBeVisible();
        await settingsBtn.click();
        const settingsDialog = page.getByRole('dialog', { name: /Settings/i });
        await expect(settingsDialog).toBeVisible({ timeout: 5000 });
        await page.keyboard.press('Escape');
        await expect(settingsDialog).toBeHidden();

        // 3. Shortcuts modal
        const shortcutsBtn = page.locator('button[aria-label="Keyboard shortcuts"]').first();
        if (await shortcutsBtn.isVisible()) {
          await shortcutsBtn.click();
          const shortcutsDialog = page.getByRole('dialog', { name: /Keyboard Shortcuts/i });
          await expect(shortcutsDialog).toBeVisible({ timeout: 5000 });
          await page.keyboard.press('Escape');
          await expect(shortcutsDialog).toBeHidden();
        }

        // 4. Command Palette
        await page.keyboard.press('Control+Shift+P');
        const palette = page.locator('.ide-palette');
        await expect(palette).toBeVisible({ timeout: 5000 });
        await page.keyboard.press('Escape');
        await expect(palette).toBeHidden();

        // 5. Activity Bar items (Explorer, Samples, Search, AST, Security, Agent Safety Lab)
        const activities = ['Explorer', 'Samples', 'Search', 'Security'];
        for (const act of activities) {
          const actBtn = page.locator(`button.ide-activity-button[aria-label="${act}"]`).first();
          if (await actBtn.isVisible()) {
            await actBtn.click();
            await page.waitForTimeout(200);
          }
        }

        // 6. Sample Browser: test clicking sample rows
        const samplesAct = page.locator('button.ide-activity-button[aria-label="Samples"]').first();
        await samplesAct.click();
        await page.waitForTimeout(400);

        const sampleRow = page.locator('button.ide-sample-row').first();
        if (await sampleRow.isVisible({ timeout: 5000 }).catch(() => false)) {
          await sampleRow.click();
          await expect.poll(async () => {
            return await page.evaluate(() => {
              const monaco = (window as any).monaco;
              const editors = monaco?.editor?.getEditors?.() || [];
              for (const ed of editors) {
                const val = ed.getModel()?.getValue();
                if (val && val.length > 0) return val;
              }
              const models = monaco?.editor?.getModels?.() || [];
              for (const m of models) {
                const val = m.getValue();
                if (val && val.length > 0) return val;
              }
              return '';
            });
          }, { timeout: 10_000 }).not.toBe('');
        }

        // 7. Panel Tabs and Panel controls (Maximise, Restore, Close)
        const panelTabs = ['Tokens', 'Security', 'Problems'];
        for (const tabName of panelTabs) {
          const tab = page.locator('.ide-tab, [role="tab"]').filter({ hasText: new RegExp(tabName, 'i') }).first();
          if (await tab.isVisible()) {
            await tab.click();
            await page.waitForTimeout(150);
          }
        }

        const maxBtn = page.locator('button[aria-label="Maximise panel"]').first();
        if (await maxBtn.isVisible()) {
          await maxBtn.click();
          await page.waitForTimeout(200);
          const restoreBtn = page.locator('button[aria-label="Restore panel"]').first();
          await expect(restoreBtn).toBeVisible();
          await restoreBtn.click();
        }

        // 8. Build with AI Drawer
        const buildBtn = page.getByRole('button', { name: 'Build with AI' }).first();
        await expect(buildBtn).toBeVisible();
        await buildBtn.click();
        const buildDrawer = page.getByRole('dialog', { name: 'Build with AI' });
        await expect(buildDrawer).toBeVisible();
        await page.keyboard.press('Escape');
        await expect(buildDrawer).toBeHidden();

        // 9. New file action
        const explorerAct = page.locator('button.ide-activity-button[aria-label="Explorer"]').first();
        await explorerAct.click();
        const newFileBtn = page.locator('button[aria-label="New file"]').first();
        if (await newFileBtn.isVisible()) {
          await newFileBtn.click();
          await page.waitForTimeout(300);
          // Verify a tab exists
          const tabs = page.locator('.ide-tab');
          expect(await tabs.count()).toBeGreaterThanOrEqual(1);
        }
      });
    }
  }
});
