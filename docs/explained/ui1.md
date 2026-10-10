# UI-1: Workspace and Editor Fundamentals

## Workspace reducer

`web/src/state/workspace.ts` models open files separately from the active editor view. `files` stores each document by stable ID, `order` preserves the tab order, and `activeId` identifies the selected tab. Editing a file compares its content with `savedContent` to derive its dirty state. A copied sample starts with `origin: "sample"`; reopening the same unmodified sample focuses its existing file, while opening it after edits creates a numbered copy. `contentVersion` advances on edits so a response for an older version can be rejected.

The reducer is a plain TypeScript function. That makes workspace transitions predictable and easy to exercise in Vitest without mounting Monaco or React.

## Monaco controlled and uncontrolled values

A controlled editor receives its contents as a React `value` prop. React then continually reconciles the model with component state. That can reset cursor, selection, and undo history when application state changes. An uncontrolled editor creates a Monaco model and keeps it alive; model change events report edits to the workspace reducer. Programmatic fixes should use model edit operations so a patch is a single undo step. A distinct model per file also preserves markers and view state while tabs change.

## Sidebar toggle placement

A toggle must remain available when its panel is hidden. If the only collapse control is inside the collapsible panel, collapsing removes the control needed to expand it. UI-1 adds a permanent Explorer rail outside that panel and a Ctrl+B shortcut. The panel remains mounted so its local state and resizable layout can be retained.

## Viva Q&A

1. **Why use a reducer?** It centralizes file transitions and gives predictable state changes that are straightforward to test.
2. **Why does each file need its own Monaco model?** Each document keeps its own text model, undo history, markers, and cursor/view state.
3. **What is the risk of a controlled Monaco value?** Reconciliation can replace model content and disrupt cursor position or undo history.
4. **How do stale analysis responses get rejected?** Each edit increments a content version; only results for the current version should be applied.
5. **Why put the Explorer toggle outside the sidebar?** A hidden panel cannot contain a usable control to reopen itself.
