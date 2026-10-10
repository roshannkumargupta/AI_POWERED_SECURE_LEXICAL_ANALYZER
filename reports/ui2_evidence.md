# UI-2 visual evidence

## Before / after

The starting state was reviewed in the running browser before edits. The updated state was reviewed in the running browser after edits; the Java SQL injection sample showed 11 findings, an enclosing `doGet` breadcrumb, a 3-step source-to-sink trace, and the verified PreparedStatement fix. The diff review showed the verifier note; applying the fix removed the original SQL finding, and Ctrl+Z restored the sample successfully.

The CUA browser screenshot API displayed before/after captures in the working session but does not expose a workspace file-save operation in this environment. Accordingly, the `docs/screenshots/before_ui2/` and `docs/screenshots/after_ui2/` folders are present but contain no claimed screenshot evidence. Capturing durable PNGs remains an acceptance item.

## Exactly what changed

- **Hidden by default:** Monaco minimap and bracket-pair colorization; detector confidence and rule metadata are collapsed under Details; false-positive reporting is under More actions; the ML tab remains behind its tab; sample picker removed from the top bar (samples remain in Explorer and the command palette).
- **Moved:** filename into the top bar beside language; current-symbol and selected-finding navigation into editor breadcrumbs; Download, keyboard help, minimap toggle, and backend reachability into the More actions menu; summary score into a compact 56 px ring with a text summary.
- **Stayed identical:** SecureLex Night palette, Monaco, Inter and JetBrains Mono, offline/local API workflow, language support, findings, taint decorations, fix review/apply, analysis, samples, and source download.

## Verification

- `npm run test`: 79 tests passed across 9 files.
- `npm run build`: passed. Vite reports the existing large Monaco bundle warning (>500 kB).
- Browser walk-through covered one Python, Java, JavaScript, and C/C++ sample. Findings and taint paths were read, fixes reviewed/applied, and Ctrl+Z restored all four samples (JavaScript/C required focusing the editor before undo). Fix all was correctly disabled because the selected remediations were review-needed; both enabled and disabled control states are component-tested.
