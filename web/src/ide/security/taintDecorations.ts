import type * as Monaco from 'monaco-editor';
import type { TaintPathV2 } from '../../api/client';

export function taintDecorations(path: TaintPathV2 | undefined, rulerLane: number): Monaco.editor.IModelDeltaDecoration[] {
  if (!path) return [];
  return path.steps.map((step, index) => ({
    range: { startLineNumber: step.range.start_line, startColumn: step.range.start_col, endLineNumber: step.range.end_line, endColumn: step.range.end_col },
    options: {
      inlineClassName: `ide-p4-flow-${step.role}`,
      before: { content: `${index + 1} `, inlineClassName: `ide-p4-flow-number ide-p4-flow-number-${step.role}` },
      overviewRuler: { color: 'var(--color-vs-purple)', position: rulerLane },
      hoverMessage: { value: `${index + 1}. ${step.role}: ${step.note || step.text}` },
    },
  }));
}
