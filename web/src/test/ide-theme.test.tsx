import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeProvider, useTheme } from '../theme/theme';
import { IDE } from '../ide/IDE';

vi.mock('../ide/lib/MonacoEditor', () => ({
  default: () => <div aria-label="Editor test stub" />,
}));

function ThemeProbe() {
  const theme = useTheme();
  return <button onClick={theme.toggleTheme}>{theme.resolved}</button>;
}
describe('P1 theme engine', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.dataset.theme = 'dark';
    document.documentElement.classList.remove('theme-light');
    document.documentElement.classList.add('dark');
  });
  it('persists theme changes and applies prototype root classes', () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );
    fireEvent.click(screen.getByRole('button'));
    expect(localStorage.getItem('securelex.theme')).toBe('light');
    expect(document.documentElement.dataset.theme).toBe('light');
    expect(document.documentElement.classList.contains('theme-light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
  it('toggles and persists with Alt+T', () => {
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );
    fireEvent.keyDown(window, { key: 't', altKey: true });
    expect(localStorage.getItem('securelex.theme')).toBe('light');
    expect(document.documentElement.dataset.theme).toBe('light');
  });
  it('initializes theme classes synchronously before app paint', async () => {
    const fs = await import('node:fs');
    const path = await import('node:path');
    const init = fs.readFileSync(path.resolve(process.cwd(), 'public/theme-init.js'), 'utf8');
    expect(init.indexOf('root.dataset.theme = resolved')).toBeLessThan(
      init.indexOf("root.classList.toggle('dark'")
    );
    expect(init).toContain("root.classList.toggle('theme-light'");
  });
  it('renders the new workbench shell and its segmented theme switch', async () => {
    render(
      <ThemeProvider>
        <IDE />
      </ThemeProvider>
    );
    expect(
      await screen.findByRole('region', { name: 'Workbench' }, { timeout: 5000 })
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Light' }));
    expect(document.documentElement.dataset.theme).toBe('light');
  });
});
