# UI-7: theme, scrolling, and scaling

## Why text can turn black

Browsers supply default colors to native controls. When an app sets a dark background but omits `color-scheme: dark` or control text colors, a button or select may keep its default black `buttontext`. SecureLex now sets the dark scheme at the root and has buttons, inputs, selects, and textareas inherit the theme color. Primary actions use a dark foreground over the light blue accent so their text keeps readable contrast.

## Why flex children need `min-height: 0`

A flex item normally keeps the minimum height of its contents. In a fixed-height IDE, a table or editor can then force its parent beyond the available space instead of scrolling inside its own panel. Setting `min-height: 0` lets the panel shrink to its allotted space; one inner element then owns scrolling. The file-tab strip also needs to stay a fixed-height sibling of the flexible editor body.

## How the fluid scale works

The scale uses `clamp(min(width/768, height/480), 1, 2)`. A user zoom choice of 0.85, 1, or 1.15 multiplies that scale. The app root is laid out at the inverse frame dimensions and transformed to fill the viewport. Existing styles are still mostly pixel-valued, so this phase scales the root frame rather than converting every component measurement to `rem`. Monaco uses a 12 px base font and its automatic layout observes the resized editor.

## What an end-to-end test proves

An end-to-end test drives the running UI through a real user flow: open a sample, analyze it, inspect a finding, apply a fix, and verify the changed editor state. It catches wiring and layout errors that a component unit test cannot. The current repository has no Playwright dependency, so the saved browser diagnostics and QA protocol are manual; the Apply-fix diff flow is not yet claimed as verified.

## Viva questions

1. **Why set `color-scheme: dark`?** It tells the browser to draw native controls and scrollbars for a dark interface.
2. **Why does a scrollable flex item need `min-height: 0`?** It lets the item shrink below its content's intrinsic height so its own overflow can scroll.
3. **How is the UI scale calculated?** It uses the smaller viewport ratio against 768×480, clamps that ratio from 1 to 2, then multiplies by the saved user zoom.
4. **Why alpha-composite backgrounds for contrast checks?** A translucent highlight blends with its parent; testing the tint as an opaque color reports the wrong text/background ratio.
5. **What extra evidence does E2E provide?** It proves the UI and backend work together through a user journey, including navigation and resulting editor state.
