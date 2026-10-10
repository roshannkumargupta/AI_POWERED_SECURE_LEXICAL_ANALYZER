import type * as monaco from 'monaco-editor';

export interface NavigationLogEntry {
  time: number;
  method: string;
  reason?: string;
  stack?: string;
}

export const navigationLog: NavigationLogEntry[] = [];

function recordCall(method: string, reason?: string): void {
  if (import.meta.env.DEV || (import.meta.env as any).VITE_E2E === '1') {
    navigationLog.push({
      time: Date.now(),
      method,
      reason,
      stack: new Error().stack,
    });
  }
}

export function focusEditor(
  editor: monaco.editor.IStandaloneCodeEditor | null,
  reason = 'user'
): void {
  if (!editor) return;
  recordCall('focus', reason);
  editor.focus();
}

export function setEditorPosition(
  editor: monaco.editor.IStandaloneCodeEditor | null,
  line: number,
  col: number,
  reason = 'user'
): void {
  if (!editor) return;
  recordCall('setPosition', reason);
  editor.setPosition({ lineNumber: line, column: col });
}

export function setEditorSelection(
  editor: monaco.editor.IStandaloneCodeEditor | null,
  selection: monaco.IRange,
  reason = 'user'
): void {
  if (!editor) return;
  recordCall('setSelection', reason);
  editor.setSelection(selection);
}

export function revealEditorRange(
  editor: monaco.editor.IStandaloneCodeEditor | null,
  range: monaco.IRange,
  reason = 'user'
): void {
  if (!editor) return;
  recordCall('revealRange', reason);
  editor.revealRangeInCenter(range);
}

export function setEditorValue(
  editor: monaco.editor.IStandaloneCodeEditor | null,
  text: string,
  reason = 'user'
): void {
  if (!editor) return;
  recordCall('setValue', reason);
  const model = editor.getModel();
  if (!model) return;
  editor.pushUndoStop();
  editor.executeEdits('securelex-navigation', [{ range: model.getFullModelRange(), text }]);
  editor.pushUndoStop();
}
