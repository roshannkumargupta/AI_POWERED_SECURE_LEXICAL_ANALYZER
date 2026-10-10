# UI-2: Progressive disclosure

SecureLex presents source code as the primary work surface. The finding inspector prioritizes the vulnerability, evidence, data flow, and remediation; detector internals and confidence detail belong in collapsed details. Summary and ML remain separate tabs so an analyst can reach them without competing with the code.

Semantic colour is consistent: blue marks actions and focus, severity hues always accompany an icon and text label, green marks verified/safe outcomes, and grey is neutral. This lets colour support the wording rather than carry meaning alone.

## Viva questions

1. **Why use progressive disclosure?** It reduces first-glance noise while keeping advanced evidence accessible in one action.
2. **Why is code the central surface?** SecureLex is an IDE workflow; findings need to be understood in their source context.
3. **Why pair severity colour with an icon and label?** It preserves meaning for colour-blind users and in low-contrast conditions.
4. **Why keep ML evidence last?** Rule and taint evidence explain the issue directly; ML is supporting evidence and may be unavailable offline.
5. **When should green appear?** Only for safe, verified, or fixed outcomes, so it does not imply that an unresolved issue is safe.
