# UI-7 feature matrix — before fixes

Evidence is limited to the original browser session at 1536×1022 and raw reports in `reports/ui7/before/`. “Partial” rows have at least one observed check but do not claim complete matrix coverage.

| ID | Status | Observation / evidence |
|---|---|---|
| D1 | FAIL | Flyout opened; root color scheme was normal; responsive and keyboard close paths not fully walked. `1536x1022-flyout-samples.json`. |
| D2 | FAIL | Empty start rendered; 22 native controls ignored the dark color scheme. `1536x1022-empty.json`. |
| D3 | Partial | Multi-file tabs were later exercised; full open/save/unsaved/512 KB flows were not captured before fixes. |
| D4 | Partial | Target and lexical demos loaded; search/edit/undo catalogue coverage not completed. |
| D5 | Partial | Python target demo selected and analyzed; all extensions/override paths not captured. |
| D6 | Partial | Monaco and 300-line document rendered; exact decorations/keyboard states not fully audited. |
| D7 | FAIL | Token-table view showed low-contrast findings and scroll concerns. `1536x1022-security-tokens.json`. |
| D8 | Partial | Explanation panel displayed a manual-fix security finding; all finding states not covered. |
| D9 | Partial | Taint, ML, Summary tabs opened; before counts show a control/theme failure. |
| D10 | Partial | Filter bar rendered; all AND combinations and keyboard paths not walked. |
| D11 | Partial | Fix all showed count; second-click/idempotence not tested. |
| D12 | Partial | Status rendered on demo; retry/failed states not induced. |
| D13 | Partial | Not all network/storage/backend/error-boundary failure states induced. |
| D14 | Partial | Python demos loaded; Java/JavaScript/C++ sample behavior not completed in baseline. |
| D15 | FAIL | Contrast/control scan failed and target viewport accessibility walk was incomplete. |
| D16 | Partial | Prior phase verification exists in `docs/STATE.md`; UI-7 rerun is recorded in the evidence report. |
