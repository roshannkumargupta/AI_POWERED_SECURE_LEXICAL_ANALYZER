import type * as monaco from 'monaco-editor';
import { Finding, TaintPathStep } from '../api/client';

export class DecorationManager {
  private editor: monaco.editor.IStandaloneCodeEditor;
  private monacoInstance: typeof monaco;
  private taintDecorationIds: string[] = [];
  private unicodeDecorationIds: string[] = [];

  constructor(editor: monaco.editor.IStandaloneCodeEditor, monacoInstance: typeof monaco) {
    this.editor = editor;
    this.monacoInstance = monacoInstance;
  }

  /**
   * Highlights a finding's taint path steps (Source -> Propagate -> Sink)
   */
  public updateTaintPath(taintSteps: TaintPathStep[] | null): void {
    if (!taintSteps || taintSteps.length === 0) {
      this.taintDecorationIds = this.editor.deltaDecorations(this.taintDecorationIds, []);
      return;
    }

    const newDecorations: monaco.editor.IModelDeltaDecoration[] = taintSteps.map((step, idx) => {
      let inlineClass = 'taint-propagate-inline';
      let glyphClass = 'taint-propagate-glyph';
      let label = 'PROPAGATE';

      if (step.step === 'source') {
        inlineClass = 'taint-source-inline';
        glyphClass = 'taint-source-glyph';
        label = 'SOURCE';
      } else if (step.step === 'sink') {
        inlineClass = 'taint-sink-inline';
        glyphClass = 'taint-sink-glyph';
        label = 'SINK';
      } else if (step.step === 'sanitizer_missing') {
        inlineClass = 'taint-propagate-inline';
        glyphClass = 'taint-propagate-glyph';
        label = 'MISSING SANITIZER';
      }

      const stepNumber = idx + 1;
      const hoverText = `**Step ${stepNumber} (${label}):** \`${step.text}\`\n\n${step.note}`;

      return {
        range: new this.monacoInstance.Range(
          step.range.start_line,
          step.range.start_col,
          step.range.end_line,
          step.range.end_col
        ),
        options: {
          isWholeLine: false,
          className: inlineClass,
          glyphMarginClassName: glyphClass,
          glyphMarginHoverMessage: { value: `Step ${stepNumber}: ${label}` },
          hoverMessage: { value: hoverText },
          overviewRuler: {
            color: step.step === 'source' ? '#5CC8FF' : step.step === 'sink' ? '#FF4D6D' : '#F5C542',
            position: this.monacoInstance.editor.OverviewRulerLane.Right,
          },
        },
      };
    });

    this.taintDecorationIds = this.editor.deltaDecorations(this.taintDecorationIds, newDecorations);
  }

  /**
   * Highlights Trojan Source and other Unicode findings with inline red decorations
   */
  public updateUnicodeDecorations(findings: Finding[]): void {
    const unicodeFindings = findings.filter(
      (f) => !f.suppressed && (f.rule_id.includes('UNI') || f.sources.includes('unicode'))
    );

    const newDecorations: monaco.editor.IModelDeltaDecoration[] = unicodeFindings.map((f) => {
      return {
        range: new this.monacoInstance.Range(
          f.range.start_line,
          f.range.start_col,
          f.range.end_line,
          f.range.end_col
        ),
        options: {
          inlineClassName: 'unicode-danger-inline',
          glyphMarginClassName: 'unicode-danger-glyph',
          hoverMessage: {
            value: `🚨 **Hidden / Dangerous Unicode Control:** ${f.title}\n\n${f.message}`,
          },
          overviewRuler: {
            color: '#FF4D6D',
            position: this.monacoInstance.editor.OverviewRulerLane.Left,
          },
        },
      };
    });

    this.unicodeDecorationIds = this.editor.deltaDecorations(
      this.unicodeDecorationIds,
      newDecorations
    );
  }

  public clearAll(): void {
    this.taintDecorationIds = this.editor.deltaDecorations(this.taintDecorationIds, []);
    this.unicodeDecorationIds = this.editor.deltaDecorations(this.unicodeDecorationIds, []);
  }
}
