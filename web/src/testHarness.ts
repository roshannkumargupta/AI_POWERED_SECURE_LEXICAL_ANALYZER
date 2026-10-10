import type * as monaco from 'monaco-editor';
import { navigationLog } from './editor/navigation';

export interface CursorLogEntry {
  t: number;
  line: number;
  col: number;
  source: string;
  reason: string;
  isAutomatic?: boolean;
}

export interface RequestLogEntry {
  url: string;
  method: string;
  t: number;
}

export interface TestHarnessState {
  activeDocId: string | null;
  isDirty: boolean;
  status: string;
  resultVersion: number;
  openDocsCount: number;
}

export class TestHarness {
  public cursorLog: CursorLogEntry[] = [];
  public requestLog: RequestLogEntry[] = [];
  public editor: monaco.editor.IStandaloneCodeEditor | null = null;
  public stateGetter: (() => TestHarnessState) | null = null;
  private lastUserGestureTime = 0;

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', () => { this.lastUserGestureTime = Date.now(); }, true);
      window.addEventListener('mousedown', () => { this.lastUserGestureTime = Date.now(); }, true);
      this.interceptFetch();
    }
  }

  private interceptFetch(): void {
    const originalFetch = window.fetch;
    const self = this;
    window.fetch = async function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
      const method = init?.method || 'GET';
      self.requestLog.push({ url, method, t: Date.now() });
      return originalFetch.apply(this, [input, init]);
    };
  }

  public recordCursorChange(line: number, col: number, source: string, reasonCode: number): void {
    const reasonMap: Record<number, string> = {
      0: 'NotSet',
      1: 'ContentFlush',
      2: 'RecoverFromMarkers',
      3: 'Explicit',
      4: 'Paste',
      5: 'Undo',
      6: 'Redo',
    };
    const reason = reasonMap[reasonCode] || 'Unknown';
    const isUserGesture = Date.now() - this.lastUserGestureTime <= 200;
    const isAutomatic = (reason === 'ContentFlush' || reason === 'Explicit') && !isUserGesture;

    this.cursorLog.push({
      t: Date.now(),
      line,
      col,
      source,
      reason,
      isAutomatic,
    });
  }

  public setEditor(editor: monaco.editor.IStandaloneCodeEditor): void {
    this.editor = editor;
  }

  public setStateGetter(getter: () => TestHarnessState): void {
    this.stateGetter = getter;
  }

  public getValue(): string {
    return this.editor?.getValue() || '';
  }

  public getModelId(): string {
    return this.editor?.getModel()?.uri.toString() || '';
  }

  public getPosition(): { line: number; col: number } {
    const pos = this.editor?.getPosition();
    return { line: pos?.lineNumber || 1, col: pos?.column || 1 };
  }

  public getSelection(): { startLine: number; startCol: number; endLine: number; endCol: number } {
    const sel = this.editor?.getSelection();
    return {
      startLine: sel?.startLineNumber || 1,
      startCol: sel?.startColumn || 1,
      endLine: sel?.endLineNumber || 1,
      endCol: sel?.endColumn || 1,
    };
  }

  public selectedText(): string {
    const sel = this.editor?.getSelection();
    const model = this.editor?.getModel();
    if (!sel || !model) return '';
    return model.getValueInRange(sel);
  }

  public setPosition(line: number, col: number): void {
    this.editor?.setPosition({ lineNumber: line, column: col });
  }

  public isReadOnly(): boolean {
    return Boolean(this.editor?.getOption(89 as monaco.editor.EditorOption.readOnly));
  }

  public getOption(name: string): any {
    return (this.editor?.getRawOptions() as any)?.[name];
  }

  public focusOwner(): { tag: string; id: string; className: string } | null {
    const el = document.activeElement;
    if (!el) return null;
    return {
      tag: el.tagName.toLowerCase(),
      id: el.id,
      className: typeof el.className === 'string' ? el.className : '',
    };
  }

  public decorationCount(kind?: string): number {
    const model = this.editor?.getModel();
    if (!model) return 0;
    const decorations = model.getAllDecorations();
    if (!kind) return decorations.length;
    return decorations.filter((d) => {
      const cls = d.options.inlineClassName || d.options.className || d.options.glyphMarginClassName || '';
      return cls.includes(kind);
    }).length;
  }

  public clearCursorLog(): void {
    this.cursorLog = [];
  }

  public clearRequestLog(): void {
    this.requestLog = [];
  }

  public getNavigationLog(): any[] {
    return navigationLog;
  }

  public state(): TestHarnessState {
    return this.stateGetter?.() || {
      activeDocId: null,
      isDirty: false,
      status: 'unknown',
      resultVersion: 0,
      openDocsCount: 0,
    };
  }
}

export const harness = new TestHarness();

declare global {
  interface Window {
    __slTest?: TestHarness;
  }
}

// Hook ONLY in DEV or VITE_E2E=1 builds
if (typeof window !== 'undefined' && (import.meta.env.DEV || (import.meta.env as any).VITE_E2E === '1')) {
  window.__slTest = harness;
}
