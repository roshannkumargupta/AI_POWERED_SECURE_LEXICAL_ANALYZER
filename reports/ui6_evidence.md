# UI-6 verification evidence

Date: 2026-10-03

## Automated checks

- `npm.cmd test` — passed, 14 files / 109 tests.
- `npm.cmd run build` — passed. Vite reports the existing large Monaco bundle advisory.
- `ruff check .` — passed.
- Plain `pytest -q` — did not collect because the system Python could not import `apsla`.
- Project virtualenv retry (`PYTHONPATH=src .venv\Scripts\python.exe -m pytest -q --basetemp=reports/.pytest-tmp`) — produced no output and did not finish in the Windows sandbox; stopped after waiting. The full Python suite is unverified for this UI-6 turn.

## Browser walkthrough

The live app was opened at `http://127.0.0.1:5173/` with its API at `http://127.0.0.1:8010/api`.

- Loaded the API sample catalogue; the flyout showed 46 Python, 36 Java, 36 JavaScript, and 35 C/C++ samples. The two Python Target Demo samples appeared before the ordinary groups.
- Opened the Target Demo Security sample and confirmed the editor, token table, selected explanation, CWE-78, ATT&CK T1059, and bottom security counts.
- Opened Target Demo Lexical Error and confirmed the malformed string appears with lexical `error`, security `n/a`, and a separate lexical finding. Selecting the bottom Lexical filter left the lexical row visible.
- Opened Summary and confirmed Score, Critical, High, and Lexical tiles. ML Insights showed the model ID and calibrated Safe/Suspicious/Malicious probabilities; Taint path showed the API-derived source, propagation, and sink steps.
- Applied Fix All Safe Issues. The backend reported one applied fix and the score changed from 36 to 61. Monaco Ctrl+Z restored the prior source.
- Confirmed open sample documents appear as separate tabs and in Files. A flyout overlap found during this walkthrough was fixed; the icon strip stays clickable with an open panel and Help switched directly from Files.
- Source scan found the only runtime `fetch` call in `web/src/api/client.ts`, which targets the configured `/api` base. No UI request to an external service was found.

Screenshots are saved at `docs/screenshots/after_ui6/security-demo.jpg`, `docs/screenshots/after_ui6/lexical-demo.jpg`, and `docs/screenshots/after_ui6/summary.jpg`.

## Visual reference limit

`docs/ui_reference/README.md` records that the requested mockup HTML and `target.png` were not supplied. Therefore no pixel measurement or `compare.png` was generated; the screenshots document the implemented UI only.
