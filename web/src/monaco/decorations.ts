import type * as monaco from 'monaco-editor';
import { Finding, TaintPathStep } from '../api/client';
import { deriveTokens } from '../tokens/derive';

const themeToken = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

export class DecorationManager {
  private editor: monaco.editor.IStandaloneCodeEditor;
  private monacoInstance: typeof monaco;
  private taintDecorationIds: string[] = [];
  private unicodeDecorationIds: string[] = [];
  private tokenDecorationIds: string[] = [];
  private securityDecorationIds: string[] = [];
  private activeModel: monaco.editor.ITextModel | null;

  constructor(editor: monaco.editor.IStandaloneCodeEditor, monacoInstance: typeof monaco) {
    this.editor = editor;
    this.monacoInstance = monacoInstance;
    this.activeModel = editor.getModel();
    editor.onDidChangeModel((event) => {
      if (this.activeModel) {
        if (this.taintDecorationIds.length) this.activeModel.deltaDecorations(this.taintDecorationIds, []);
        if (this.unicodeDecorationIds.length) this.activeModel.deltaDecorations(this.unicodeDecorationIds, []);
        if (this.tokenDecorationIds.length) this.activeModel.deltaDecorations(this.tokenDecorationIds, []);
        if (this.securityDecorationIds.length) this.activeModel.deltaDecorations(this.securityDecorationIds, []);
      }
      this.tokenDecorationIds = [];
      this.securityDecorationIds = [];
      this.taintDecorationIds = [];
      this.unicodeDecorationIds = [];
      this.activeModel = event.newModelUrl ? this.editor.getModel() : null;
    });
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
            color: step.step === 'source' ? themeToken('--flow-source') : step.step === 'sink' ? themeToken('--flow-sink') : themeToken('--flow-propagate'),
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
            color: themeToken('--sev-critical'),
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
    this.tokenDecorationIds = this.editor.deltaDecorations(this.tokenDecorationIds, []);
    this.securityDecorationIds = this.editor.deltaDecorations(this.securityDecorationIds, []);
  }

  public updateTokenMap(mode: 'off'|'security'|'full', result: Parameters<typeof deriveTokens>[0] | null, selectedIndex: number | null, category = ''): void {
    if ((mode === 'off' && !category) || !result) { this.tokenDecorationIds = this.editor.deltaDecorations(this.tokenDecorationIds, []); return; }
    const derived = deriveTokens(result);
    const selected = selectedIndex === null ? null : derived[selectedIndex];
    const marks = derived.filter((t) => category ? t.categories.includes(category) : mode === 'security' ? t.securityRelevant : selected?.index === t.index).map((t) => ({
      range: new this.monacoInstance.Range(t.range.start_line,t.range.start_col,t.range.end_line,t.range.end_col),
      options: { inlineClassName: mode === 'full' ? 'token-map-selected' : t.role === 'Source' ? 'token-map-source' : t.role === 'Sink' ? 'token-map-sink' : 'token-map-security', glyphMarginClassName: mode === 'security' ? (t.role === 'Source' ? 'token-map-glyph-source' : t.role === 'Sink' ? 'token-map-glyph-sink' : 'token-map-glyph') : undefined, hoverMessage: { value: `${t.lexicalType} · ${t.role} · ${t.severity}` } },
    }));
    this.tokenDecorationIds = this.editor.deltaDecorations(this.tokenDecorationIds, marks);
  }

  public updateSecurityDecorations(result: Parameters<typeof deriveTokens>[0] | null, selectedIndex: number | null): void {
    if (!result) { this.securityDecorationIds = this.editor.deltaDecorations(this.securityDecorationIds, []); return; }
    const decorations: monaco.editor.IModelDeltaDecoration[] = deriveTokens(result).flatMap((token) => {
      const className = selectedIndex === token.index ? 'sl-selected' : token.relatedFindings.some((finding) => finding.kind === 'lexical') ? 'sl-lexerr' : token.securityRelevant ? 'sl-insecure' : '';
      if (!className) return [];
      const messages = token.relatedFindings.map((finding) => finding.message).filter(Boolean);
      return [{
        range: new this.monacoInstance.Range(token.range.start_line, token.range.start_col, token.range.end_line, token.range.end_col),
        options: { inlineClassName: className, hoverMessage: messages.length ? [{ value: `${messages[0]}\n\nClick for details` }] : undefined },
      }];
    });
    this.securityDecorationIds = this.editor.deltaDecorations(this.securityDecorationIds, decorations);
  }
}
