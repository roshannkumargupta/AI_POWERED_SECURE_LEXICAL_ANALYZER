# UI-1 Browser QA Checklist

Run against a local frontend and API, saving captures under `docs/screenshots/after_ui1/`.

| Check | Result |
|---|---|
| Empty first load and Auto-detect selector | Pass in live browser |
| New file then type/paste | Pass for typing; paste not checked |
| Explorer rail and Ctrl+B close/reopen | Ctrl+B pass both directions; rail click not verified |
| Sample model editing and undo | Editing pass; Ctrl+Z attempt did not undo the edit; redo not checked |
| Samples grouped by language | Pass: Java selection filtered to 4 Java samples |
| Show all languages | Pass: expanded all four language groups and displayed 17 samples |
| Open multiple files / folder / drag and drop | Not implemented or verified |
| Ctrl+S download / dirty close confirmation | Not verified |
| Java SQL injection analysis | Pass: live API returned 11 findings, including critical APS-JV-INJ-002 |
| Quick fix and Fix all, then undo | Not verified |
| Stop/restart API and automatic recovery | Not verified |
| Refresh warning with unsaved changes | Not verified |
| Resize all panels; F8 / Shift+F8 | Not verified |
| Large paste | Not verified |
| Frontend build | Pass |
| Vitest | Pass: 20 tests |
| Ruff and pytest | Not run in this UI pass |
