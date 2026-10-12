# SecureLex UI rules (every UI phase reads this first)

BASE: web/ui-reference/prototype.html is the visual source of truth. Keep its look,
spacing, colours and structure. Rebuild it as real React + TypeScript components wired
to the real backend. Never copy its fake data or behaviour.

LAYOUT (px): title bar 38 | activity bar 48 | explorer 240 | editor tab bar 34 |
sub-toolbar 30 | editor/panel split 48%/52% with 5px drag resizer | bottom tab bar 32 |
token inspector 310 (collapsible) | status bar 24 | Build-with-AI drawer 360 (slides from
right, between title bar and status bar) | Safety Lab columns 320 / flexible / 380 |
Fix modal max-width 896, max-height 90vh. Base font 13px, code line height 22px.
Inter (UI) + JetBrains Mono (code, tables) + Material Symbols Outlined icons, all
bundled locally. No CDN, no external request at runtime.

THEMES: <html> carries data-theme="dark|light" plus class "dark" or "theme-light".
All colours are the CSS variables of the prototype (--color-vs-*, --body-bg, --card-*,
--status-bar-*, scrollbar and gutter vars): copy both blocks verbatim into
web/src/theme/tokens.css. Toggle = segmented Dark/Light control in the title bar +
activity-bar toggle + Alt+T. Persist in localStorage (try/catch), apply before first
paint (web/public/theme-init.js), Monaco theme follows. No hard-coded hex in components.

REAL DATA ONLY:
- No hard-coded counts, versions, timings, compiler names, project names, dates,
  success messages, or words like "secure", "100%", "compliant", "verified" unless the
  backend result says so. Every number is derived from API data.
- Unavailable tool/model/feature -> visible "unavailable" state with setup guidance.
  Never a fake result. No alert(), no fake window controls (- [] x), no fake minimap.
- Wording constants: "No findings detected by checks run", "Analysis incomplete",
  "Check unavailable", "Potential vulnerability", "Finding detected". The words
  "Verified for specified checks" appear only when the verifier outcome equals it.
- Source code, lexemes, filenames, tool output and model output are untrusted: render as
  text only. Never innerHTML / dangerouslySetInnerHTML. Show hidden characters as <U+XXXX>.
- Analysis is manual by default (Analyze / F5 / Ctrl+Enter). Editing marks results stale.
  No automatic cursor moves; programmatic selection/focus only in the navigation module.

WORKFLOW: one phase per chat, branch ui/pN, small commits, tag ui-pN at the end.
After every phase run and show real output of:
  cd web && npm run typecheck && npm run lint && npm test && npm run build
  cd .. && ruff check . && pytest -q && python scripts/golden.py --check
Fix failures; never skip or weaken tests. Backend changes only when the UI needs them,
additive, with tests, golden check green. Never edit data/ or src/apsla/ml/artifacts/.
End each phase with a short summary of what changed plus the real command output in the
chat (no report files, no screenshots saved into the repo except under /tmp).
If any file named in a prompt is missing: print pwd and ls, name the missing path, and
stop. Never ask me to paste file contents.
