import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export type ThemeMode = 'dark' | 'light' | 'system';
export type ResolvedTheme = 'dark' | 'light';
export const THEME_STORAGE_KEY = 'securelex.theme';

function readMode(): ThemeMode {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
  } catch { /* Storage can be unavailable; the in-memory mode still works. */ }
  return 'dark';
}

function resolveMode(mode: ThemeMode): ResolvedTheme {
  return mode === 'system'
    ? (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : mode;
}

function applyTheme(mode: ThemeMode, resolved: ResolvedTheme) {
  const root = document.documentElement;
  root.classList.add('theme-switching');
  root.dataset.theme = resolved;
  root.dataset.themeMode = mode;
  const meta = document.querySelector<HTMLMetaElement>('meta[name="color-scheme"]');
  if (meta) meta.content = resolved;
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove('theme-switching')));
}

interface ThemeContextValue {
  mode: ThemeMode;
  resolved: ResolvedTheme;
  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}
const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(readMode);
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(() => resolveMode('system'));
  const resolved = mode === 'system' ? systemTheme : mode;

  useEffect(() => {
    const query = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!query) return;
    const update = (event: MediaQueryListEvent | MediaQueryList) => {
      const next = event.matches ? 'dark' : 'light';
      if (document.documentElement.dataset.themeMode === 'system') applyTheme('system', next);
      setSystemTheme(next);
    };
    update(query);
    query.addEventListener?.('change', update);
    return () => query.removeEventListener?.('change', update);
  }, []);

  useEffect(() => { applyTheme(mode, resolved); }, [mode, resolved]);

  const setMode = useCallback((next: ThemeMode) => {
    applyTheme(next, resolveMode(next));
    setModeState(next);
    try { localStorage.setItem(THEME_STORAGE_KEY, next); } catch { /* In-memory mode remains active. */ }
  }, []);
  const toggleTheme = useCallback(() => setMode(resolved === 'dark' ? 'light' : 'dark'), [resolved, setMode]);
  const value = useMemo(() => ({ mode, resolved, setMode, toggleTheme }), [mode, resolved, setMode, toggleTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error('useTheme must be used within ThemeProvider');
  return value;
}
