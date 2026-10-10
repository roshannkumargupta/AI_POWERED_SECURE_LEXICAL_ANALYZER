# SecureLex demo path

Follow these steps in order. Select each sample in SAMPLES, run Analyze if the result has not appeared, and keep the Finding panel visible.

| Step | Sample | What to click | What to say (two sentences) | Audience should see |
|---:|---|---|---|---|
| 1 | `py-i01` | Expand Python → Intermediate; open the sample. | “This request parameter is untrusted. The command reaches a shell sink.” | APS-PY-INJ-002, taint path, reviewable fix, Demo notes match. |
| 2 | `py-s02` | Open the safe Python sample. | “This look-alike still uses a shell API. Quoting the input changes the analyzer result.” | No medium finding; safe comparison. |
| 3 | `py-u04` | Open the confusable API sample. | “The function name uses Cyrillic look-alikes. Unicode analysis exposes the disguise.” | Unicode and code execution findings. |
| 4 | `py-u01` | Open the bidi sample. | “These controls affect visual reading order. The source remains ordinary text in the editor.” | Unicode finding and code-point notes. |
| 5 | `py-b06` | Open the YAML sample. | “The unsafe loader can construct arbitrary objects. The proposed fix uses a safer loader.” | Deserialization finding and fix. |
| 6 | `py-a06` | Open the multi-issue service. | “This larger route combines several bug classes. Fix all only applies verified eligible changes.” | Multiple findings, Fix all state, and ML Insights tab. |
| 7 | `jv-i01` | Switch to Java and open the servlet sample. | “Request data flows into a dynamic query. The Java plugin shows the relevant rule.” | SQL finding and any taint explanation available. |
| 8 | `jv-i06` | Open the Java file sample. | “The path comes from request input. Review the path handling finding and suggested remediation.” | File/path finding. |
| 9 | `js-b04` | Switch to JavaScript and open the sample. | “A browser value is written to an unsafe HTML sink. The scanner identifies the XSS rule.” | XSS finding and taint details if available. |
| 10 | `js-a01` | Open the advanced JavaScript sample. | “This sample combines application-level patterns. Compare the source and finding explanations.” | Advanced finding(s), fix eligibility and ML Insights. |
| 11 | `cp-i01` | Switch to C/C++ and open the sample. | “The argument is untrusted and copied to a fixed buffer. The taint path connects source to sink.” | APS-CP-MEM-001 and taint path. |
| 12 | `cp-a06` | Open the bounds-check comparison. | “One path checks the length before copying. The unchecked function remains flagged.” | APS-CP-MEM-001 only for the unchecked copy. |
| 13 | `py-a04` | Return to Python and open the harmless decoded-message sample. | “The encoded content is deliberately inert. Obfuscation detection helps review hidden behavior.” | APS-PY-OBF-001 and final Demo notes. |

The current manifest ships all 13 listed entries. Sample source is inert; use only the sample text and do not execute it.
