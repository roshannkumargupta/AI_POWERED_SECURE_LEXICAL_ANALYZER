import { expect, type Page } from '@playwright/test';

export async function handleConsent(page: Page) {
  const scrimBtn = page
    .locator('.ide-consent-scrim button, .ide-ai-consent button')
    .filter({ hasText: /Allow/i });
  if (await scrimBtn.isVisible({ timeout: 600 }).catch(() => false)) {
    await scrimBtn.first().click();
    await page.waitForTimeout(400);
    return;
  }
  const allowBtn = page.getByRole('button', { name: /Allow/i });
  if (await allowBtn.isVisible({ timeout: 600 }).catch(() => false)) {
    await allowBtn.first().click();
    await page.waitForTimeout(400);
  }
}

export async function setEditorText(page: Page, text: string) {
  await page.locator('.monaco-editor').first().waitFor({ state: 'visible', timeout: 20_000 });
  const textarea = page.locator('.monaco-editor textarea').first();
  await textarea.focus();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.keyboard.insertText(text);
  await page.waitForTimeout(400);
}

export async function getEditorText(page: Page): Promise<string> {
  return await page.evaluate(() => {
    const monaco = (window as any).monaco;
    const model = monaco?.editor?.getModels?.()[0];
    return model ? model.getValue() : '';
  });
}
