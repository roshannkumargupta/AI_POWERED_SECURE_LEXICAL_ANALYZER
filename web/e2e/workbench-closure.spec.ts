import { expect, test, type Page } from '@playwright/test';

async function closeBy(page: Page, surface: string, method: 'x' | 'escape' | 'backdrop', xLabel: RegExp, backdrop: string) {
  if (method === 'x') await page.getByRole('button', { name: xLabel }).click();
  else if (method === 'escape') await page.keyboard.press('Escape');
  else await page.locator(backdrop).click({ position: { x: 5, y: 5 } });
  await expect(page.locator(surface)).toHaveCount(0);
}

test('Settings, New File, shortcuts, palette, AI drawer and consent close through all routes', async ({ page }) => {
  await page.route('**/api/capabilities', async route => {
    const response = await route.fetch();
    const data = await response.json();
    data.features.build_with_ai = true;
    data.ai.provider = 'test-remote';
    data.ai.configured = true;
    data.ai.reachable = true;
    data.ai.model_present = true;
    data.ai.consent_required = true;
    data.ai.remote_consented = false;
    data.ai.processing_location = 'remote';
    await route.fulfill({ response, json: data });
  });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Settings' })).toBeVisible();

  for (const method of ['x', 'escape', 'backdrop'] as const) {
    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByRole('dialog', { name: 'Workbench Settings' })).toBeVisible();
    await closeBy(page, '.ide-p4-modal-scrim', method, /Close settings/, '.ide-p4-modal-scrim');

    await page.keyboard.press('Control+N');
    await expect(page.getByRole('dialog', { name: 'New File' })).toBeVisible();
    await closeBy(page, '.ide-overlay', method, /Close New File dialog/, '.ide-overlay');

    await page.keyboard.press('F1');
    await expect(page.getByRole('dialog', { name: 'Keyboard Shortcuts' })).toBeVisible();
    await closeBy(page, '.ide-modal-overlay', method, /Close Keyboard Shortcuts/, '.ide-modal-overlay');

    await page.getByRole('button', { name: 'Open Command Palette (Ctrl+Shift+P)' }).click();
    await expect(page.getByRole('dialog', { name: 'Command Palette' })).toBeVisible();
    await closeBy(page, '.ide-palette', method, /Close Command Palette/, '.ide-overlay');

    await page.getByRole('button', { name: 'Build with AI' }).click();
    await expect(page.getByRole('dialog', { name: 'Build with AI' })).toBeVisible();
    await page.getByLabel('Requirements').fill('Create a small offline test candidate.');
    await page.getByRole('button', { name: 'Generate' }).click();
    await expect(page.getByRole('dialog', { name: 'Remote processing consent' })).toBeVisible();
    if (method === 'backdrop') await closeBy(page, '.ide-consent-scrim', method, /Close consent/, '.ide-consent-scrim');
    else await closeBy(page, '.ide-ai-consent', method, /Close consent/, '.ide-consent-scrim');
    await closeBy(page, '.ide-build-drawer', method, /Close drawer/, '.ide-drawer-backdrop');
  }
});

test('pending Fix proposal always closes and aborts when dismissed', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Language/ }).click();
  await page.getByRole('option', { name: 'Python' }).click();
  const editorInput = page.locator('.monaco-editor textarea').first();
  await editorInput.focus();
  await page.keyboard.press('Control+A');
  await page.keyboard.type('print("unterminated');
  await page.keyboard.press('End');
  await page.keyboard.press('Backspace');
  await page.keyboard.press('Backspace');
  await page.getByRole('button', { name: 'Analyze' }).click();
  const fixToken = page.getByRole('button', { name: /Fix invalid token/ });
  await expect(fixToken).toBeEnabled();
  await page.route('**/api/fixes/propose', async route => {
    await new Promise(resolve => setTimeout(resolve, 1800));
    try { await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Test proposal delay ended.' }) }); } catch { /* Closing the modal aborts this request. */ }
  });

  for (const method of ['x', 'escape', 'backdrop'] as const) {
    await fixToken.click();
    await expect(page.locator('.ide-fix-modal')).toContainText('Preparing proposal');
    await closeBy(page, '.ide-fix-modal', method, /Close fix review/, '.ide-fix-overlay');
  }
});

test('panel max-close-reopen, tab actions, sidebar collapse and Safety Lab Escape work without reload', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Maximise panel' }).click();
  await expect(page.locator('.ide-panel.maximised')).toBeVisible();
  await page.getByRole('button', { name: 'Close panel' }).click();
  await expect(page.locator('.ide-panel')).toHaveCount(0);
  await page.keyboard.press('Control+J');
  await expect(page.locator('.ide-panel')).toBeVisible();
  await expect(page.locator('.ide-panel.maximised')).toHaveCount(0);

  await page.keyboard.press('Control+N');
  await expect(page.getByLabel('New file language')).toHaveValue('python');
  await page.getByLabel('New file language').selectOption('python');
  await page.getByLabel('File name').fill('second.py');
  await expect(page.getByLabel('File name')).toHaveValue('second.py');
  await page.getByRole('button', { name: 'Create' }).click();
  await expect(page.locator('.ide-tab')).toHaveCount(2);
  await page.locator('.ide-tab').first().click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Close Others' }).click();
  await expect(page.locator('.ide-tab')).toHaveCount(1);
  await page.locator('.ide-tab').first().click({ button: 'right' });
  await expect(page.getByRole('menuitem', { name: 'Copy Name' })).toBeVisible();
  await expect(page.getByRole('menuitem', { name: /Copy Path/ })).toBeDisabled();
  await page.keyboard.press('Escape');

  await page.getByRole('button', { name: 'Explorer' }).click();
  await expect(page.getByLabel('explorer sidebar')).toHaveCount(0);
  await page.keyboard.press('Control+B');
  await expect(page.getByLabel('explorer sidebar')).toBeVisible();

  await page.getByRole('button', { name: 'Agent Safety Lab' }).click();
  await expect(page.locator('.ide-safety-lab')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.ide-safety-lab')).toHaveCount(0);
});
