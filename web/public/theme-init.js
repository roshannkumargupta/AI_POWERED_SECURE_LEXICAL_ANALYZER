(() => {
  let mode = 'dark';
  try {
    const saved = localStorage.getItem('securelex.theme');
    if (saved === 'dark' || saved === 'light' || saved === 'system') mode = saved;
  } catch { /* Fall back to the dark default when storage is blocked. */ }
  const resolved = mode === 'system'
    ? (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : mode;
  const root = document.documentElement;
  root.dataset.theme = resolved;
  root.dataset.themeMode = mode;
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) meta.content = resolved;
})();
