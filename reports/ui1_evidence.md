# UI-1 Evidence

Date: October 2, 2026

## Verified in the browser

- First load showed an empty editor state, no active sample, and the language selector set to Auto-Detect.
- Opening the Python sample loaded its code into Monaco. Typing `\n# edited` updated the visible model contents.
- The permanent Explorer control reported pressed/unpressed state. Ctrl+B hid the sidebar and a second Ctrl+B restored it.
- The sidebar New file action changed the language back to Auto-detect. The first check found stale Monaco text after this transition; a model sync was added, and a new check confirmed typing `print('hello')` into the empty editor.
- The Java SQL injection sample filtered the sidebar to four Java samples. The live analyzer returned 11 findings (including critical `APS-JV-INJ-002`) for the bundled sample; typing into that sample changed the editor model.
- Ctrl+Z did not visibly undo the sample edit in the browser. Undo/redo is a known outstanding failure despite the Monaco model change; it needs a focused follow-up before acceptance.
- On a fresh empty workspace, the sidebar showed four collapsed language groups; **Show all languages** expanded the 17 available samples across Python, Java, JavaScript, and C/C++.
- The API response captures were refreshed from the running local server: 4 languages, 17 samples, and analysis payloads for one vulnerable Python and one vulnerable Java sample (2 and 11 findings, respectively). Files are in `docs/api_samples/`.
- Build: `npm.cmd run build` succeeded (Vite warned that the main chunk exceeds 500 KB).
- Frontend tests: `npm.cmd test` passed, 20 tests across 7 files.
- Ruff: `ruff check .` passed. `ruff format --check .` found 3 unformatted files under `scratch/`.
- Pytest: full suite completed with one failure: `tests/unit/test_cpp_syntax.py::test_balanced_preprocessor_conditionals`.

## Not verified / blocked

- The first API startup attempts used port 8000 and `scripts/dev.py` generated Windows multiprocessing `PermissionError: [WinError 5]` logs. The Vite proxy in `web/vite.config.ts` targets port 8001. Starting Uvicorn directly on 8001 restored API connectivity and allowed fresh captures and a live Java analysis.
- Quick fix, Fix all, backend stop/restart recovery, and delayed retry behavior remain unverified.
- The browser check covered initial state, Java sample editing, new buffer typing, language-filtered samples, live analysis, and Ctrl+B close/reopen. File/folder IO, drag and drop, undo/redo, panel resizing, large paste, F8, backend recovery, and beforeunload were not completed.
- `docs/screenshots/before_ui1/` contains pre-existing initial, sample, collapsed-sidebar, and feature captures. `docs/screenshots/after_ui1/` has only its placeholder; no after screenshots were saved by the browser tool in this pass.
- `docs/api_samples/` had pre-existing JSON response captures before this task. They were not replaced because the API could not be called reliably.

See `docs/ui_qa_checklist.md` for the remaining manual pass.
