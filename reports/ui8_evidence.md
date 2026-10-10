# UI-8 Verification Evidence: Light, Dark, and System Appearance

Date: 2026-10-09  
Phase: UI-8 — Dark / Light / System Theme Switch with WCAG AA Contrast Guarantee

---

## 1. Automated Test Execution

### 1.1 Web Test Suite (`npm test --prefix web`)
* **Status**: **PASS** (17 test files, 118 unit tests passed).
* **Token Parity & Source Reference Test** (`web/src/test/ui8-theme.test.ts`):
  * Verified that both `:root[data-theme="dark"]` and `:root[data-theme="light"]` declare identical custom properties.
  * Verified that every `var(--*)` referenced in the web application codebase maps to an existing token.
  * Verified that no hardcoded palette colors (`#hex`, `rgba()`, `hsla()`, or named colors outside `tokens.css`) exist in component files.
* **WCAG Contrast Ratios**:
  * Body copy and muted text (`--text-primary`, `--text-secondary`, `--text-muted`) on `--surface-1`, `--surface-2`, and `--surface-3` meet $\ge 4.5:1$ in both dark and light modes.
  * Interactive accents (`--text-accent`) on `--surface-1`, `--surface-2`, and `--bg-accent` meet $\ge 4.5:1$.
  * State feedback pairs (`text-success` on `bg-success`, `text-warning` on `bg-warning`, `text-danger` on `bg-danger`, `text-neutral` on `bg-neutral`) meet $\ge 4.5:1$.
  * Unified diff highlights (`diff-add-fg` on `diff-add-bg`, `diff-del-fg` on `diff-del-bg`) meet $\ge 4.5:1$.
  * Severity indicators (`--sev-critical`, `--sev-high`, `--sev-medium`, `--sev-low`, `--sev-info`) on surfaces meet $\ge 4.5:1$.
  * Interactive borders (`--border-control`) and focus rings (`--focus-ring`) meet $\ge 3:1$ against surface backgrounds.

### 1.2 Web Production Build (`npm run build --prefix web`)
* **Status**: **PASS** (`tsc && vite build`).
* Bundled assets including Monaco Editor web workers, fonts, and theme-init script successfully emitted to `web/dist/`.

### 1.3 Python Code Integrity (`ruff check .`)
* **Status**: **PASS** (100% clean, zero lint or formatting issues).

---

## 2. PART G Defect Remediations & Regression Results

| Item | Defect Description | Resolution & Verification |
|---|---|---|
| **G1** | DOM XSS finding (`APS-JS-XSS-001`) grouped as "Malicious" | Updated `findingGroup` in `web/src/model/adapt.ts` so high/critical severity findings are mapped to **"Dangerous"**, reserving "Malicious" strictly for findings carrying explicit malicious tags. Verified in `web/src/test/ui5-adapt.test.ts`. |
| **G2** | First body row overlapping sticky header in token table | Resolved table border model in `web/src/ui5.css`: replaced `border-collapse: collapse` with `border-collapse: separate; border-spacing: 0;`, giving `thead th` sticky positioning with `z-index: 2`, `background: var(--surface-1)`, and a dedicated border box shadow. Verified no body row occlusion across viewports. |
| **G3** | Non-anchor tokens inside finding range marked insecure | Enforced strict anchor lexeme matching (`anchorsRow`) in `web/src/model/adapt.ts` so punctuation, operators, and peripheral tokens are marked safe, while only the true sink (e.g. `element.innerHTML`) is flagged. Regression tested against `js-i09` in `web/src/test/ui5-adapt.test.ts`. |
| **G4** | Status bar pill alignment and spacing | Standardized `pillStyle` baseline metrics (`lineHeight: 16px`, `padding: 1px 7px`, inline-flex alignment) and applied uniform 8px gap across telemetry chips in `web/src/components/StatusBar.tsx`. |

---

## 3. Theme Engine & Runtime Behavior (STEP 2–4)

* **Flash-Free Pre-Paint Init**: Added `web/public/theme-init.js`, loaded synchronously in `<head>` before stylesheets and bundles. Reads `securelex.theme` from `localStorage`, resolves `system` via `matchMedia`, and applies `data-theme` and `color-scheme` before the first frame paint.
* **Dynamic Monaco Theme Generator**: Implemented `buildMonacoTheme` in `web/src/theme/monacoTheme.ts`, dynamically computing Monaco editor theme tokens from active CSS variables without reloading models, preserving cursor position, undo/redo history, scroll offsets, and active decorations.
* **TopBar Controls**: Added 32px icon toggle button (`Sun`/`Moon`) immediately preceding the More actions menu with `aria-live` announcement.
* **Help Flyout**: Added Appearance segmented radio selector (`Dark` \| `Light` \| `System`), displaying system preference state when in System mode.
* **Command Palette**: Registered `Theme: Dark`, `Theme: Light`, `Theme: System`, and `Toggle theme` actions.
* **Resilience**: Handled blocked/restricted `localStorage` gracefully with in-memory state fallbacks.

---

## 4. Diagnostics & Geometry Proof (STEP 5)

* **Diagnostics Script (`web/qa/diagnostics.js`)**:
  * Updated background alpha compositing to dynamically select theme root backdrop (`#FFFFFF` in light mode, `#1A1A19` in dark mode).
  * Updated native controls inspection to validate against the active theme's `color-scheme` without generating false positives on light surfaces.
  * Ran at target viewports (1280×720, 1366×768, 1536×864, 1536×1022, 1920×1080) in both dark and light modes; all checks produced verdict **PASS** (zero `lowContrast`, zero `blackOnDark`, zero `nativeControls`, zero `scrollBugs`).
* **Geometry Invariance**:
  * Evaluated via `web/qa/ref_metrics.mjs`. Bounding-box metrics for TopBar, Select, Analyze/FixAll buttons, Icon Strip, File Tabs, and Status Bar matched within 0.5px between Dark and Light modes, confirming that theme switching modifies colors strictly without altering layout geometry or component sizing.
