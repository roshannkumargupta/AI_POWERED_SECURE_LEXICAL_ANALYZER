# UI-1 audit

Audited against the live Vite app at `http://127.0.0.1:5173/` and the current `web/src` tree. The existing baseline captures in `docs/screenshots/before_ui1/` cover initial load, a clicked sample, collapsed sidebar, and the available feature view. API response captures in `docs/api_samples/` were already present at audit start; the attempt to refresh them against the local API failed because the backend process exited during startup.

`EditorPane.tsx` passed `value={source}` and `onChange` into Monaco. No `readOnly` prop or `readOnly` option was found. Initial source was `BUNDLED_SAMPLES[0].code` in `store.ts`; sample selection dispatched global `SET_SOURCE`/language/filename actions from `App.tsx`. Sidebar collapse used `display:none` on the panel, while the only expand control was rendered inside `Sidebar.tsx`.

| Bug | Reproduction | Root cause (file:line) | Planned fix |
|---|---|---|---|
| Sidebar cannot reopen | Click “Collapse Sidebar”; the sidebar disappears and no rail remains in the main layout. | `web/src/App.tsx:364-379` hides the panel with `display:none`; its only expand control lives inside `Sidebar.tsx:34-51`. | Permanent outside rail; keep panel mounted and toggle/collapse imperatively. |
| Samples are not editable / typing resets | Click any sample, then type or paste into Monaco. | Sample selection replaces global source in `App.tsx:306-311`; `EditorPane.tsx:247-249` passes React state as controlled `value` and writes each model change back, causing whole-value resets and losing model-local undo state. No `readOnly` prop was found. | Per-file Monaco model; listen to model content events, never feed controlled values back to Monaco. |
| No New File command | Inspect top bar/sidebar; only local file input is available. | `Sidebar.tsx:59-77`; `TopBar.tsx:59-173`. | Add File actions and create empty untitled buffer with keyboard shortcuts. |
| Samples all mixed | Open sidebar or Samples menu with multiple sample languages. | `Sidebar.tsx:95-128` maps all samples; `TopBar.tsx:105-123` maps all samples. | Filter/group by effective language, labels, search and Show all. |
| Python sample starts by default | Reload app. | `web/src/state/store.ts:78-83` assigns `BUNDLED_SAMPLES[0]` to initial state. | Start without an active file and display language Auto-detect. |
| General IDE workflows are incomplete | Try tab switching, multi-file open/save, folder, drag/drop, close dirty file, offline recovery. | Single-buffer state in `web/src/state/store.ts:27-50`; file input is single-select in `Sidebar.tsx:75-87`; one global analysis/source in `App.tsx:103-118`. | Add workspace model, file commands, per-file results, safe IO and reliable retry handling. |
| Simplification / restyle | Would require visual redesign beyond these behavior fixes. | Explicitly scoped to UI-2. | No visual restyle in UI-1. |

## Other required repros

The live page showed the Python sample populated on first load and the language selector set to Python 3. Backend health showed unavailable after the attempted `scripts/dev.py` startup; browser-visible analysis returned an “Internal Server Error” toast. Because no stable backend was running, analyzer-dependent interactions (analysis markers, quick fixes, Fix all, and recovery) could not be verified in this audit pass. File editing/undo, hover, F8, resizing, language changes, large paste, file drag/drop, and refresh warning are listed for the acceptance pass after the fixes.

## API follow-up

The initial API failure was resolved during implementation: `web/vite.config.ts` targets port 8001, while the attempted `scripts/dev.py` command starts on 8000. Direct Uvicorn on 8001 returned live responses. Refreshed captures now show 4 languages, 17 samples, 2 findings for the vulnerable Python sample, and 11 for the vulnerable Java sample. Browser testing confirmed Java sample analysis and per-language filtering. Remaining analyzer-dependent acceptance checks are listed in `reports/ui1_evidence.md`.
