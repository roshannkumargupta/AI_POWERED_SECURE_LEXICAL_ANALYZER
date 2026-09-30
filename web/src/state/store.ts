import React, { createContext, useContext, useReducer, useEffect } from 'react';
import {
  AnalysisResult,
  Finding,
  Fix,
  LanguageInfo,
  MLInsightsResponse,
  SampleItem,
  Severity,
} from '../api/client';
import { BUNDLED_SAMPLES } from '../samples';

export interface ToastItem {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  actionLabel?: string;
  onAction?: () => void;
  durationMs?: number;
}

export interface DiffModalData {
  isOpen: boolean;
  fix: Fix | null;
  finding: Finding | null;
  oldSource: string;
  newSource: string;
  diff: string;
}

export interface AppState {
  source: string;
  language: string;
  filename: string;
  analysis: AnalysisResult | null;
  isAnalyzing: boolean;
  isBackendAvailable: boolean;
  selectedFindingId: string | null;
  selectedTokenIndex: number | null;
  mlInsights: MLInsightsResponse | null;
  isLoadingInsights: boolean;
  activeTab: 'finding' | 'summary' | 'ml';
  problemsFilter: 'all' | Severity;
  cursorPosition: { line: number; col: number };
  toasts: ToastItem[];
  diffModal: DiffModalData | null;
  activeDataFlowFindingId: string | null;
  isSidebarCollapsed: boolean;
  languages: LanguageInfo[];
  samples: SampleItem[];
}

export type Action =
  | { type: 'SET_SOURCE'; payload: string }
  | { type: 'SET_LANGUAGE'; payload: string }
  | { type: 'SET_FILENAME'; payload: string }
  | { type: 'SET_ANALYZING'; payload: boolean }
  | { type: 'SET_ANALYSIS'; payload: AnalysisResult }
  | { type: 'SET_BACKEND_AVAILABLE'; payload: boolean }
  | { type: 'SELECT_FINDING'; payload: string | null }
  | { type: 'SELECT_TOKEN_INDEX'; payload: number | null }
  | { type: 'SET_ML_INSIGHTS'; payload: MLInsightsResponse | null }
  | { type: 'SET_LOADING_INSIGHTS'; payload: boolean }
  | { type: 'SET_ACTIVE_TAB'; payload: 'finding' | 'summary' | 'ml' }
  | { type: 'SET_PROBLEMS_FILTER'; payload: 'all' | Severity }
  | { type: 'SET_CURSOR_POSITION'; payload: { line: number; col: number } }
  | { type: 'ADD_TOAST'; payload: Omit<ToastItem, 'id'> & { id?: string } }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'OPEN_DIFF_MODAL'; payload: Omit<DiffModalData, 'isOpen'> }
  | { type: 'CLOSE_DIFF_MODAL' }
  | { type: 'SET_DATA_FLOW'; payload: string | null }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_LANGUAGES'; payload: LanguageInfo[] }
  | { type: 'SET_SAMPLES'; payload: SampleItem[] }
  | { type: 'HIDE_FINDING'; payload: string };

const initialSample = BUNDLED_SAMPLES[0];

export const initialState: AppState = {
  source: initialSample.code,
  language: initialSample.language,
  filename: initialSample.filename,
  analysis: null,
  isAnalyzing: false,
  isBackendAvailable: true,
  selectedFindingId: null,
  selectedTokenIndex: null,
  mlInsights: null,
  isLoadingInsights: false,
  activeTab: 'summary',
  problemsFilter: 'all',
  cursorPosition: { line: 1, col: 1 },
  toasts: [],
  diffModal: null,
  activeDataFlowFindingId: null,
  isSidebarCollapsed: false,
  languages: [
    { id: 'python', display_name: 'Python 3', extensions: ['.py'], monaco_id: 'python' },
    { id: 'java', display_name: 'Java', extensions: ['.java'], monaco_id: 'java' },
    { id: 'javascript', display_name: 'JavaScript', extensions: ['.js', '.jsx'], monaco_id: 'javascript' },
    { id: 'cpp', display_name: 'C++', extensions: ['.cpp', '.cc', '.h'], monaco_id: 'cpp' },
  ],
  samples: BUNDLED_SAMPLES,
};

export function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_SOURCE':
      return { ...state, source: action.payload };

    case 'SET_LANGUAGE':
      return { ...state, language: action.payload };

    case 'SET_FILENAME':
      return { ...state, filename: action.payload };

    case 'SET_ANALYZING':
      return { ...state, isAnalyzing: action.payload };

    case 'SET_ANALYSIS': {
      const activeFindings = action.payload.findings.filter((f) => !f.suppressed);
      const stillSelected = activeFindings.find((f) => f.id === state.selectedFindingId);
      return {
        ...state,
        analysis: action.payload,
        isAnalyzing: false,
        selectedFindingId: stillSelected ? stillSelected.id : activeFindings[0]?.id || null,
        activeDataFlowFindingId:
          state.activeDataFlowFindingId &&
          activeFindings.find((f) => f.id === state.activeDataFlowFindingId)
            ? state.activeDataFlowFindingId
            : null,
      };
    }

    case 'SET_BACKEND_AVAILABLE':
      return { ...state, isBackendAvailable: action.payload };

    case 'SELECT_FINDING':
      return {
        ...state,
        selectedFindingId: action.payload,
        activeTab: action.payload ? 'finding' : state.activeTab,
      };

    case 'SELECT_TOKEN_INDEX':
      return { ...state, selectedTokenIndex: action.payload };

    case 'SET_ML_INSIGHTS':
      return {
        ...state,
        mlInsights: action.payload,
        isLoadingInsights: false,
      };

    case 'SET_LOADING_INSIGHTS':
      return { ...state, isLoadingInsights: action.payload };

    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };

    case 'SET_PROBLEMS_FILTER':
      return { ...state, problemsFilter: action.payload };

    case 'SET_CURSOR_POSITION':
      return { ...state, cursorPosition: action.payload };

    case 'ADD_TOAST': {
      const id = action.payload.id || Math.random().toString(36).substring(2, 9);
      const newToast: ToastItem = { ...action.payload, id };
      return { ...state, toasts: [...state.toasts, newToast] };
    }

    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.payload) };

    case 'OPEN_DIFF_MODAL':
      return {
        ...state,
        diffModal: { ...action.payload, isOpen: true },
      };

    case 'CLOSE_DIFF_MODAL':
      return { ...state, diffModal: null };

    case 'SET_DATA_FLOW':
      return {
        ...state,
        activeDataFlowFindingId: action.payload,
        selectedFindingId: action.payload || state.selectedFindingId,
        activeTab: action.payload ? 'finding' : state.activeTab,
      };

    case 'TOGGLE_SIDEBAR':
      return { ...state, isSidebarCollapsed: !state.isSidebarCollapsed };

    case 'SET_LANGUAGES':
      return { ...state, languages: action.payload };

    case 'SET_SAMPLES':
      return { ...state, samples: action.payload };

    case 'HIDE_FINDING': {
      if (!state.analysis) return state;
      const updatedFindings = state.analysis.findings.filter((f) => f.id !== action.payload);
      return {
        ...state,
        analysis: {
          ...state.analysis,
          findings: updatedFindings,
        },
        selectedFindingId:
          state.selectedFindingId === action.payload
            ? updatedFindings[0]?.id || null
            : state.selectedFindingId,
        activeDataFlowFindingId:
          state.activeDataFlowFindingId === action.payload ? null : state.activeDataFlowFindingId,
      };
    }

    default:
      return state;
  }
}

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Auto-dismiss toasts after duration
  useEffect(() => {
    if (state.toasts.length === 0) return;
    const latestToast = state.toasts[state.toasts.length - 1];
    const duration = latestToast.durationMs ?? 4000;
    const timer = setTimeout(() => {
      dispatch({ type: 'REMOVE_TOAST', payload: latestToast.id });
    }, duration);
    return () => clearTimeout(timer);
  }, [state.toasts]);

  return React.createElement(AppContext.Provider, { value: { state, dispatch } }, children);
};

export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
