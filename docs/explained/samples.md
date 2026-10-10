# Why the sample catalogue matters

A security analyzer needs examples with known properties. The catalogue makes expected behavior repeatable: a vulnerable sample should trigger the stated rule, while a safe sample should remain below the medium threshold. It also makes regressions visible when rules, taint tracking, fixes, or language plugins change.

## How to read evaluation outcomes

- **True positive:** a vulnerable sample is flagged for the expected issue.
- **False positive:** a safe sample is flagged as vulnerable.
- **False negative:** a vulnerable sample is missed.

Safe look-alikes contain suspicious words or APIs in a bounded or harmless context. If those stay clean, they provide evidence that the analyzer is distinguishing behavior from keywords, which helps measure precision. Basic, intermediate, and advanced levels introduce the rule, show common source-to-sink flows, and combine multiple patterns; safe, Unicode, and lexer groups cover additional review tasks.

## Viva questions

1. **Why keep an explicit expected rule ID?** It makes each sample a reproducible check and reveals when a detector silently stops matching its documented behavior.
2. **What does a false positive mean?** A safe example was flagged, which can reduce trust and add alert fatigue.
3. **Why include pending samples?** They preserve the requested scenario and record a verified engine gap without weakening the expected result.
4. **Why include safe look-alikes?** They test whether the analyzer uses code context instead of matching suspicious words alone.
5. **Why separate sample levels?** They let reviewers learn one pattern at a time before inspecting longer flows and combined issues.
