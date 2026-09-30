import type * as monaco from 'monaco-editor';
import { Finding } from '../api/client';

export interface HoverActionHandlers {
  onQuickFix?: (findingId: string) => void;
  onShowDataFlow?: (findingId: string) => void;
}

let activeHandlers: HoverActionHandlers = {};

export function setHoverActionHandlers(handlers: HoverActionHandlers) {
  activeHandlers = handlers;
}

// Global command registration for hover links
let commandsRegistered = false;
export function registerHoverCommands(monacoInstance: typeof monaco) {
  if (commandsRegistered) return;
  commandsRegistered = true;

  monacoInstance.editor.registerCommand('securelex.quickFix', (_accessor, args: string) => {
    try {
      const data = JSON.parse(decodeURIComponent(args));
      if (data?.findingId && activeHandlers.onQuickFix) {
        activeHandlers.onQuickFix(data.findingId);
      }
    } catch (e) {
      console.error('Failed to parse quickFix command args', e);
    }
  });

  monacoInstance.editor.registerCommand('securelex.showDataFlow', (_accessor, args: string) => {
    try {
      const data = JSON.parse(decodeURIComponent(args));
      if (data?.findingId && activeHandlers.onShowDataFlow) {
        activeHandlers.onShowDataFlow(data.findingId);
      }
    } catch (e) {
      console.error('Failed to parse showDataFlow command args', e);
    }
  });
}

function isPointInRange(line: number, col: number, finding: Finding): boolean {
  const r = finding.range;
  if (line < r.start_line || line > r.end_line) {
    return false;
  }
  if (line === r.start_line && col < r.start_col) {
    return false;
  }
  if (line === r.end_line && col >= r.end_col) {
    return false;
  }
  return true;
}

export function createHoverProvider(
  getFindings: () => Finding[],
  monacoInstance: typeof monaco
): monaco.languages.HoverProvider {
  registerHoverCommands(monacoInstance);

  return {
    provideHover(_model, position) {
      const findings = getFindings().filter((f) => !f.suppressed);
      const matchingFindings = findings.filter((f) =>
        isPointInRange(position.lineNumber, position.column, f)
      );

      if (matchingFindings.length === 0) {
        return null;
      }

      const contents: monaco.IMarkdownString[] = [];

      for (const f of matchingFindings) {
        const severityIcons: Record<string, string> = {
          critical: '🔴',
          high: '🟠',
          medium: '🟡',
          low: '🔵',
          info: '⚪',
        };
        const icon = severityIcons[f.severity] || '⚠️';
        const sourcesText = f.sources?.length ? f.sources.join(' + ') : 'rule';
        const confPercent = Math.round(f.confidence * 100);

        const lines = [
          `### ${icon} **${f.title}** \`[${f.rule_id}]\``,
          `---`,
          `**Severity:** **${f.severity.toUpperCase()}** &nbsp;|&nbsp; **CWE:** [${f.cwe}](https://cwe.mitre.org/data/definitions/${f.cwe.replace('CWE-', '')}.html) &nbsp;|&nbsp; **Confidence:** ${confPercent}%`,
          ``,
          f.explanation || f.message,
          ``,
          `**Why?** Detectors fired: \`${sourcesText}\``,
        ];

        // Action links
        const actionLinks: string[] = [];
        if (f.fixes && f.fixes.length > 0) {
          const quickFixArgs = encodeURIComponent(JSON.stringify({ findingId: f.id }));
          actionLinks.push(`[⚡ **Quick fix**](command:securelex.quickFix?${quickFixArgs})`);
        }
        if (f.taint_path && f.taint_path.length > 0) {
          const flowArgs = encodeURIComponent(JSON.stringify({ findingId: f.id }));
          actionLinks.push(`[🔍 **Show data flow** (${f.taint_path.length} steps)](command:securelex.showDataFlow?${flowArgs})`);
        }

        if (actionLinks.length > 0) {
          lines.push(``, `---`, actionLinks.join(' &nbsp;&nbsp;•&nbsp;&nbsp; '));
        }

        contents.push({
          value: lines.join('\n'),
          isTrusted: true,
          supportHtml: true,
        });
      }

      const primary = matchingFindings[0];
      return {
        range: new monacoInstance.Range(
          primary.range.start_line,
          primary.range.start_col,
          primary.range.end_line,
          primary.range.end_col
        ),
        contents,
      };
    },
  };
}
