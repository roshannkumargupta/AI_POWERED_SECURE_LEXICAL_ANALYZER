import type * as monaco from 'monaco-editor';
import { Finding, Severity } from '../api/client';

export const MARKER_OWNER = 'securelex';
export const MARKER_SOURCE = 'SecureLex';

export function severityToMarkerSeverity(
  severity: Severity,
  monacoInstance: typeof monaco
): monaco.MarkerSeverity {
  switch (severity) {
    case 'critical':
    case 'high':
      return monacoInstance.MarkerSeverity.Error;
    case 'medium':
      return monacoInstance.MarkerSeverity.Warning;
    case 'low':
      return monacoInstance.MarkerSeverity.Info;
    case 'info':
    default:
      return monacoInstance.MarkerSeverity.Hint;
  }
}

export function findingToMarker(
  finding: Finding,
  monacoInstance: typeof monaco
): monaco.editor.IMarkerData {
  return {
    source: MARKER_SOURCE,
    code: finding.rule_id,
    severity: severityToMarkerSeverity(finding.severity, monacoInstance),
    message: `${finding.title}: ${finding.message}`,
    startLineNumber: finding.range.start_line,
    startColumn: finding.range.start_col,
    endLineNumber: finding.range.end_line,
    endColumn: finding.range.end_col,
  };
}

export function updateMonacoMarkers(
  model: monaco.editor.ITextModel,
  findings: Finding[],
  monacoInstance: typeof monaco
): void {
  const activeFindings = findings.filter((f) => !f.suppressed);
  const markers = activeFindings.map((f) => findingToMarker(f, monacoInstance));
  monacoInstance.editor.setModelMarkers(model, MARKER_OWNER, markers);
}

export function clearMonacoMarkers(
  model: monaco.editor.ITextModel,
  monacoInstance: typeof monaco
): void {
  monacoInstance.editor.setModelMarkers(model, MARKER_OWNER, []);
}
