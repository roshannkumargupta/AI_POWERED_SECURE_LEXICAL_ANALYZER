# SL2-8b Evidence

Date: 2026-10-12

## Implemented

- Added an analysis workspace surface with Problems, Security, AST, AI Explain, Agent Activity, Build with AI, Fix with AI, Safety Lab, Settings and Export views. These views call the existing v2 endpoints; API errors are shown verbatim from the service and no view inserts sample results.
- Problems loads the lexical and syntax endpoints and groups returned diagnostics. Security loads the security-stage response and exposes its real finding evidence, provenance, tool status and taint path steps. AST requests syntax with an AST and expands nodes through the AST endpoint.
- AI views use `/api/capabilities`, remote-consent API state and provider readiness. Build posts to `/api/ai/generate` and opens the returned code in a new `AI candidate.<language>` editor file; the backend analysis, assumptions and requirements checklist are shown in the drawer.
- Fix actions use `/api/fixes/propose`, `/verify`, `/apply` and `/undo`. A proposal alone does not mutate the source; applying uses the backend approval and verification response. Applying and undoing update the active editor document.
- Safety Lab executes an actual selected `/api/agent-safety/run` request and loads the returned run result. Exports download the response of `/api/reports/export`. Added palette actions and documented Ctrl+Shift shortcuts.
- Added a four-test SL2-8b component/API interaction selection. The component relies on normal React text rendering for source, model and tool strings.

## Commands and results

`npm run test` (working directory `web/`): **exit 0**

```text
Test Files  23 passed (23)
Tests       152 passed (152)
Duration    43.77s
```

`npm run build` (working directory `web/`): **exit 0**

```text
✓ 2678 modules transformed.
dist/assets/index-BwOiZMHI.js 3,665.85 kB │ gzip: 959.34 kB
✓ built in 1m 14s
```

Vite reports the existing application bundle is larger than 500 kB after minification (3,664.30 kB in this build); this is a build warning, not a build failure.

`npm run e2e` (working directory `web/`): **exit 1; browser connection blocked before test execution**

```text
Error running matrix: TypeError: fetch failed
connect EACCES 127.0.0.1:9222
```

Browser attempt to open `http://127.0.0.1:5173/`: `Browser Use cannot open ... Browser reported: net::ERR_CONNECTION_TIMED_OUT`.

Direct API/frontend probe: PowerShell `Invoke-WebRequest` to `http://127.0.0.1:8010/api/health` and `http://127.0.0.1:5173/` each returned `An attempt was made to access a socket in a way forbidden by its access permissions.`

## Not verified / unavailable

- The real-backend golden path for Python, Java, JavaScript and C++ could not run because the sandbox denies loopback sockets, including the configured API/frontend ports and Chrome DevTools port 9222. No pass is claimed for real-browser API flows.
- Cross-theme diagnostics at five viewports could not run without the browser connection. The Vitest theme/contrast unit checks passed, which is not a substitute for the requested viewport browser matrix.
- Requested per-view screenshots for light and dark themes were not captured; no placeholder or fabricated screenshots were written. See `docs/screenshots/sl2_8b/README.md` for the host limitation.
- No configured reachable Ollama model was available according to `docs/STATE.md`; live Explain, Generate, AI Fix and LIVE Safety Lab remain unverified. Their unavailable/consent states are displayed from capability responses.
- `npm run e2e` is the repository's existing UI-9 CDP matrix runner. It failed before opening a page, so no four-language interaction was attempted or asserted.

## Scope

No backend, `legacy/`, `data/`, or `ml/artifacts/` files were changed for this phase. Git branch/tag operations were not performed; the current branch is `sl2-0` and prior project state documents the Git metadata as read-only.
