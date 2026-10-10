# UI-8: Light and dark appearance

## Design tokens and semantic colors

SecureLex keeps its colors in CSS custom properties. The dark and light theme blocks provide the same token names, so panels, controls, findings, diffs, and editor decorations can use semantic roles instead of embedding color values in components. Blue marks actions and focus; red, amber, and green are reserved for labeled security or verification states. The light palette uses cool grey surfaces and dark charcoal text rather than pure black.

## Why Monaco has a separate theme object

Monaco renders its editor, line numbers, selection, diagnostics, hover cards, suggestions, and scrollbar outside the normal DOM styles. CSS variables do not style those editor surfaces directly. `buildMonacoTheme` therefore reads the active CSS token values and builds Monaco's native theme object from that same palette. Changing the editor theme does not replace its model, so text, cursor, selection, scroll position, undo history, and decorations remain attached to the same editor state.

## Avoiding a flash of the wrong theme

The saved mode is read by a small same-origin script in the document head before the React bundle loads. It sets the resolved theme and native `color-scheme` before the browser paints native controls. React then owns subsequent mode changes and listens for system preference changes while System mode is selected.

## Contrast and WCAG

The theme test computes relative luminance and contrast ratios for the required token pairs. Body text and status labels target at least 4.5:1; focus indicators and control borders target at least 3:1. Severity is expressed with both text and color so color is not the only signal. Contrast tests are executable checks, not a substitute for reviewing real text over translucent backgrounds and screenshots.

## Viva questions

1. **Why use semantic tokens instead of putting hex values in each component?**  A single role can be tuned for both themes and remains consistent across panels, controls, and dialogs.
2. **Why does Monaco need a separate theme object?**  Monaco paints its editor surfaces in its own rendering layer and consumes its own `IStandaloneThemeData` API.
3. **How does the app prevent a wrong-theme flash?**  A synchronous, same-origin head script sets the theme before the stylesheet and application code render.
4. **What does a 4.5:1 contrast ratio mean?**  It is the WCAG AA minimum contrast target for ordinary text against its background.
5. **How does System mode react to a preference change?**  It subscribes to `prefers-color-scheme` and updates the active CSS and Monaco themes without replacing the editor model.
