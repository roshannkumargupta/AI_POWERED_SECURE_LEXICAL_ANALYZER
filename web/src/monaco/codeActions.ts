import type * as monaco from 'monaco-editor';
import { Finding, Fix } from '../api/client';

export interface CodeActionHandlers {
  onOpenDiffView?: (fix: Fix, finding: Finding) => void;
  onShowManualAdvice?: (fix: Fix, finding: Finding) => void;
}

let activeActionHandlers: CodeActionHandlers = {};

export function setCodeActionHandlers(handlers: CodeActionHandlers) {
  activeActionHandlers = handlers;
}

let codeActionCommandsRegistered = false;
export function registerCodeActionCommands(monacoInstance: typeof monaco) {
  if (codeActionCommandsRegistered) return;
  codeActionCommandsRegistered = true;

  monacoInstance.editor.registerCommand(
    'securelex.openDiff',
    (_accessor, fix: Fix, finding: Finding) => {
      if (activeActionHandlers.onOpenDiffView) {
        activeActionHandlers.onOpenDiffView(fix, finding);
      }
    }
  );

  monacoInstance.editor.registerCommand(
    'securelex.showAdvice',
    (_accessor, fix: Fix, finding: Finding) => {
      if (activeActionHandlers.onShowManualAdvice) {
        activeActionHandlers.onShowManualAdvice(fix, finding);
      }
    }
  );
}

function intersectsRange(
  r1: monaco.Range,
  r2: { start_line: number; start_col: number; end_line: number; end_col: number }
): boolean {
  if (r1.endLineNumber < r2.start_line || r1.startLineNumber > r2.end_line) {
    return false;
  }
  if (r1.endLineNumber === r2.start_line && r1.endColumn < r2.start_col) {
    return false;
  }
  if (r1.startLineNumber === r2.end_line && r1.startColumn > r2.end_col) {
    return false;
  }
  return true;
}

export function createCodeActionProvider(
  getFindings: () => Finding[],
  monacoInstance: typeof monaco
): monaco.languages.CodeActionProvider {
  registerCodeActionCommands(monacoInstance);

  return {
    provideCodeActions(model, range, _context) {
      const findings = getFindings().filter((f) => !f.suppressed);
      const matchingFindings = findings.filter((f) =>
        intersectsRange(range, f.range)
      );

      const actions: monaco.languages.CodeAction[] = [];

      for (const finding of matchingFindings) {
        if (!finding.fixes || finding.fixes.length === 0) continue;

        for (const fix of finding.fixes) {
          const verifiedBadge = fix.verification?.verified ? '✓ [Verified]' : '⚠ [Unverified]';
          const title = `${verifiedBadge} ${fix.title} (${fix.confidence.toUpperCase()})`;

          if (fix.confidence === 'safe' && fix.edits && fix.edits.length > 0) {
            // Apply atomically as a single undoable workspace edit
            const workspaceEdits: monaco.languages.IWorkspaceTextEdit[] = fix.edits.map(
              (edit) => ({
                resource: model.uri,
                textEdit: {
                  range: new monacoInstance.Range(
                    edit.range.start_line,
                    edit.range.start_col,
                    edit.range.end_line,
                    edit.range.end_col
                  ),
                  text: edit.new_text,
                },
                versionId: model.getVersionId(),
              })
            );

            actions.push({
              title: `⚡ ${title}`,
              kind: 'quickfix',
              isPreferred: true,
              edit: {
                edits: workspaceEdits,
              },
            });
          } else if (fix.confidence === 'review') {
            // Review fix triggers the DiffView
            actions.push({
              title: `🔍 Review & Apply: ${title}`,
              kind: 'quickfix',
              isPreferred: false,
              command: {
                id: 'securelex.openDiff',
                title: 'Review Fix in Diff View',
                arguments: [fix, finding],
              },
            });
          } else {
            // Manual advice
            actions.push({
              title: `ℹ️ Manual Advice: ${title}`,
              kind: 'quickfix',
              isPreferred: false,
              command: {
                id: 'securelex.showAdvice',
                title: 'Show Remediation Advice',
                arguments: [fix, finding],
              },
            });
          }
        }
      }

      return {
        actions,
        dispose: () => {},
      };
    },
  };
}
