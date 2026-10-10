import type { AnalysisResult } from '../api/client';

export type WorkspaceLanguage = 'auto' | 'python' | 'java' | 'javascript' | 'cpp';
export interface WorkspaceFile {
  id: string;
  name: string;
  language: WorkspaceLanguage;
  detectedLanguage: Exclude<WorkspaceLanguage, 'auto'> | null;
  content: string;
  savedContent: string;
  dirty: boolean;
  origin: 'new' | 'opened' | 'sample';
  sampleId?: string;
  result: AnalysisResult | null;
  resultVersion: number;
  contentVersion: number;
  status: 'idle' | 'analyzing' | 'error';
  error?: string;
}

export interface WorkspaceState {
  files: Record<string, WorkspaceFile>;
  order: string[];
  activeId: string | null;
  sidebar: { open: boolean; width: number };
  problemsOpen: boolean;
  inspectorTab: 'finding' | 'summary' | 'ml';
}

export const initialWorkspaceState: WorkspaceState = {
  files: {}, order: [], activeId: null, sidebar: { open: true, width: 240 },
  problemsOpen: true, inspectorTab: 'summary',
};

export type WorkspaceAction =
  | { type: 'newFile'; id: string; name?: string }
  | { type: 'openFiles'; files: Array<{ id: string; name: string; content: string; language?: WorkspaceLanguage }> }
  | { type: 'openSample'; id: string; name: string; content: string; language: WorkspaceLanguage; sampleId: string }
  | { type: 'closeFile'; id: string }
  | { type: 'closeAll' }
  | { type: 'switchFile'; id: string }
  | { type: 'edit'; id: string; content: string }
  | { type: 'setLanguage'; id: string; language: WorkspaceLanguage }
  | { type: 'setResult'; id: string; result: AnalysisResult | null; version: number }
  | { type: 'setStatus'; id: string; status: WorkspaceFile['status']; error?: string }
  | { type: 'markSaved'; id: string }
  | { type: 'toggleSidebar' }
  | { type: 'setSidebarWidth'; width: number }
  | { type: 'setInspectorTab'; tab: WorkspaceState['inspectorTab'] }
  | { type: 'toggleProblems' };

const languageFromName = (name: string): WorkspaceLanguage => {
  const ext = name.toLowerCase().split('.').pop();
  if (ext === 'py') return 'python';
  if (ext === 'java') return 'java';
  if (['js', 'mjs', 'cjs', 'jsx'].includes(ext || '')) return 'javascript';
  if (['c', 'h', 'cc', 'cpp', 'cxx', 'hpp'].includes(ext || '')) return 'cpp';
  return 'auto';
};

const makeFile = (id: string, name: string, content: string, origin: WorkspaceFile['origin'], language?: WorkspaceLanguage, sampleId?: string): WorkspaceFile => ({
  id, name, language: language ?? languageFromName(name), detectedLanguage: null, content, savedContent: content,
  dirty: false, origin, sampleId, result: null, resultVersion: -1, contentVersion: 0, status: 'idle',
});

export function workspaceReducer(state: WorkspaceState, action: WorkspaceAction): WorkspaceState {
  const active = (file: WorkspaceFile) => ({ ...state, files: { ...state.files, [file.id]: file }, activeId: file.id });
  switch (action.type) {
    case 'newFile': {
      const name = action.name || `untitled-${state.order.length + 1}`;
      const file = makeFile(action.id, name, '', 'new');
      return { ...active(file), order: [...state.order, file.id] };
    }
    case 'openFiles': {
      let next = state;
      const added: string[] = [];
      for (const item of action.files) {
        const existing = next.order.map((id) => next.files[id]).find((f) => f.name === item.name && !f.dirty && f.content === item.content);
        if (existing) { next = { ...next, activeId: existing.id }; continue; }
        const file = makeFile(item.id, item.name, item.content, 'opened', item.language);
        next = { ...next, files: { ...next.files, [file.id]: file }, activeId: file.id };
        added.push(file.id);
      }
      return { ...next, order: [...state.order, ...added] };
    }
    case 'openSample': {
      const same = state.order.map((id) => state.files[id]).find((f) => f.sampleId === action.sampleId && !f.dirty);
      if (same) return { ...state, activeId: same.id };
      const base = action.name.replace(/\.[^.]+$/, '');
      const count = state.order.map((id) => state.files[id]).filter((f) => f.sampleId === action.sampleId).length;
      const name = count ? `${base} (${count + 1})${action.name.match(/\.[^.]+$/)?.[0] || ''}` : action.name;
      const file = makeFile(action.id, name, action.content, 'sample', action.language, action.sampleId);
      return { ...active(file), order: [...state.order, file.id] };
    }
    case 'closeFile': {
      const order = state.order.filter((id) => id !== action.id);
      const { [action.id]: _closed, ...files } = state.files;
      const activeId = state.activeId === action.id ? order[Math.max(0, state.order.indexOf(action.id) - 1)] ?? null : state.activeId;
      return { ...state, files, order, activeId };
    }
    case 'closeAll': return { ...state, files: {}, order: [], activeId: null };
    case 'switchFile': return state.files[action.id] ? { ...state, activeId: action.id } : state;
    case 'edit': {
      const file = state.files[action.id]; if (!file) return state;
      return { ...state, files: { ...state.files, [action.id]: { ...file, content: action.content, dirty: action.content !== file.savedContent, contentVersion: file.contentVersion + 1, status: 'idle' } } };
    }
    case 'setLanguage': {
      const file = state.files[action.id]; if (!file) return state;
      return { ...state, files: { ...state.files, [action.id]: { ...file, language: action.language, resultVersion: -1 } } };
    }
    case 'setResult': {
      const file = state.files[action.id]; if (!file || action.version !== file.contentVersion) return state;
      return { ...state, files: { ...state.files, [action.id]: { ...file, result: action.result, resultVersion: action.version, status: 'idle', error: undefined } } };
    }
    case 'setStatus': {
      const file = state.files[action.id]; if (!file) return state;
      return { ...state, files: { ...state.files, [action.id]: { ...file, status: action.status, error: action.error } } };
    }
    case 'markSaved': {
      const file = state.files[action.id]; if (!file) return state;
      return { ...state, files: { ...state.files, [action.id]: { ...file, savedContent: file.content, dirty: false } } };
    }
    case 'toggleSidebar': return { ...state, sidebar: { ...state.sidebar, open: !state.sidebar.open } };
    case 'setSidebarWidth': return { ...state, sidebar: { ...state.sidebar, width: Math.max(180, Math.min(420, action.width)) } };
    case 'setInspectorTab': return { ...state, inspectorTab: action.tab };
    case 'toggleProblems': return { ...state, problemsOpen: !state.problemsOpen };
    default: return state;
  }
}

export function guessLanguage(text: string, name = ''): Exclude<WorkspaceLanguage, 'auto'> | null {
  const byName = languageFromName(name);
  if (byName !== 'auto') return byName;
  if (/^\s*#!.*\bpython\b/m.test(text) || /\b(def\s+\w+\s*\(|self\s*\.)/.test(text)) return 'python';
  if (/\b(public\s+class|import\s+java\.)/.test(text)) return 'java';
  if (/\b(function\s+\w+|const\s+\w+\s*=|require\s*\(|=>)/.test(text)) return 'javascript';
  if (/#include\s*</.test(text) || /\bint\s+main\s*\(/.test(text)) return 'cpp';
  return null;
}

export function filterSamples<T extends { language: string; title: string }>(samples: T[], language: string | null, query = '', showAll = false): T[] {
  const q = query.trim().toLocaleLowerCase();
  return samples.filter((sample) => (showAll || !language || sample.language === language) && (!q || sample.title.toLocaleLowerCase().includes(q)));
}
