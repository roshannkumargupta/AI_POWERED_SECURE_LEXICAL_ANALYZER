# UI-8 theme implementation and color audit

## Scope

Add Dark, Light, and System appearance modes while keeping layout and component sizing stable. The dark palette stays the default; CSS custom properties are the palette source for web components and Monaco.

## Color audit and semantic tokens

| Surface or source | Existing values / location | Theme token mapping |
|---|---|---|
| Global surfaces, borders, text, status badges | `web/src/theme/tokens.css:1-15` | `--surface-*`, `--border*`, `--text-*`, `--bg-*` |
| Global selection, focus, lexical and taint marks | `web/src/theme/tokens.css:36-43` | `--bg-accent`, `--focus-ring`, severity and flow tokens |
| Monaco editor, hover, suggest, gutter, selection | `web/src/theme/monacoTheme.ts:1-37` | `--surface-*`, `--text-*`, `--editor-*`, `--sev-*`, scrollbar tokens |
| Security finding and token badge groups | `web/src/components/FindingPanel.tsx`, `web/src/components/TokensPanel.tsx`, `web/src/ui5.css` | `--bg-danger/warning/success`, `--text-danger/warning/success`, `--sev-*` |
| Diff additions, deletions, and context | `web/src/components/DiffView.tsx` | `--diff-add-*`, `--diff-del-*`, `--diff-context-bg` |
| Modal and command-palette scrims/shadows | `web/src/App.tsx`, `web/src/components/CommandPalette.tsx`, `web/src/components/DiffView.tsx` | `--scrim`, `--scrim-strong`, `--shadow-*` |
| Flyouts, toolbar menus, toasts, empty-state actions | `web/src/components/TopBar.tsx`, `web/src/components/Toast.tsx`, `web/src/components/EmptyState.tsx`, `web/src/ui5.css` | `--surface-*`, `--border*`, `--accent-wash`, `--shadow-popover` |
| Taint-path step markers and Unicode overview ruler | `web/src/components/TaintPath.tsx`, `web/src/monaco/decorations.ts` | `--flow-source`, `--flow-propagate`, `--flow-sink`, `--sev-critical` |
| Startup background and SVG favicon | `web/index.html` | Explicit first-paint and brand-color exceptions; runtime surfaces use tokens |

The palette definitions live in `web/src/theme/tokens.css`; the inline startup style in `web/index.html` intentionally sets only the pre-paint dark/light root background and `color-scheme`. The embedded favicon retains its static brand stroke. Components and Monaco do not carry independent palette literals. `transparent` and `color-mix(..., transparent)` are structural alpha-compositing values.

## Verification plan

- Keep both theme blocks in token parity and validate every `var(--name)` reference.
- Check required WCAG contrast pairs programmatically in both themes.
- Exercise toolbar toggle, Help radio group, palette commands, reload persistence, system preference, and Monaco theme updates.
- Run frontend tests/build plus the existing QA diagnostics and reference metrics at the requested viewports.
- Capture comparable dark/light states and report any unavailable baseline or browser-only checks explicitly.
