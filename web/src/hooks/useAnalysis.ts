import { useRef, useCallback, useEffect } from 'react';
import { api } from '../api/client';
import { AppState, Action } from '../state/store';
import { DocItem } from '../model/doc';

interface UseAnalysisOptions {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  activeDocId: string | null;
  setOpenDocs: React.Dispatch<React.SetStateAction<DocItem[]>>;
  analyzeWhileTyping: boolean;
}

export function useAnalysis({
  state,
  dispatch,
  activeDocId,
  setOpenDocs,
  analyzeWhileTyping,
}: UseAnalysisOptions) {
  const abortControllerRef = useRef<AbortController | null>(null);
  const analysisRequestRef = useRef(0);
  const debounceTimerRef = useRef<number | null>(null);
  const lastAnalyzedSourceRef = useRef<string | null>(null);

  const currentContextRef = useRef({
    source: state.source,
    language: state.language,
    filename: state.filename,
  });
  currentContextRef.current = {
    source: state.source,
    language: state.language,
    filename: state.filename,
  };

  const runAnalysis = useCallback(
    async (sourceCode: string, targetLanguage: string, targetFilename: string) => {
      if (!sourceCode.trim()) {
        abortControllerRef.current?.abort();
        dispatch({ type: 'CLEAR_ANALYSIS' });
        return;
      }

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const requestId = ++analysisRequestRef.current;
      const targetDocId = activeDocId;

      dispatch({ type: 'SET_ANALYZING', payload: true });
      setOpenDocs((docs) =>
        docs.map((d) => (d.id === targetDocId ? { ...d, status: 'analysing' } : d))
      );

      try {
        const res = await api.analyze(
          {
            source: sourceCode,
            language: targetLanguage === 'auto' ? null : targetLanguage,
            filename: targetFilename,
            options: { fixes: true, ml: true, include_tokens: true, agent: state.agentMode },
          },
          controller.signal
        );

        if (
          controller.signal.aborted ||
          requestId !== analysisRequestRef.current ||
          currentContextRef.current.source !== sourceCode
        ) {
          if (requestId === analysisRequestRef.current) {
            dispatch({ type: 'SET_ANALYZING', payload: false });
          }
          return;
        }

        dispatch({ type: 'SET_ANALYSIS', payload: res });
        lastAnalyzedSourceRef.current = sourceCode;
        dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: true });
        setOpenDocs((docs) =>
          docs.map((d) =>
            d.id === targetDocId
              ? {
                  ...d,
                  analysis: res,
                  resultVersion: d.contentVersion,
                  status: 'analysed',
                  durationMs: res.engine?.elapsed_ms,
                }
              : d
          )
        );
      } catch (err: any) {
        if (
          err.name === 'AbortError' ||
          controller.signal.aborted ||
          requestId !== analysisRequestRef.current
        ) {
          return;
        }

        dispatch({ type: 'SET_ANALYZING', payload: false });
        dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: false });
        setOpenDocs((docs) =>
          docs.map((d) =>
            d.id === targetDocId
              ? { ...d, status: 'error', errorMessage: err.detail || err.message }
              : d
          )
        );
        dispatch({
          type: 'ADD_TOAST',
          payload: {
            message: err.detail || 'Backend unreachable. Running offline.',
            type: 'warning',
          },
        });
      }
    },
    [dispatch, activeDocId, state.agentMode]
  );

  useEffect(() => {
    if (!analyzeWhileTyping) return;
    if (debounceTimerRef.current) {
      window.clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = window.setTimeout(() => {
      runAnalysis(state.source, state.language, state.filename);
    }, 600);

    return () => {
      if (debounceTimerRef.current) {
        window.clearTimeout(debounceTimerRef.current);
      }
    };
  }, [state.source, state.language, state.filename, analyzeWhileTyping, runAnalysis]);

  const loadTokenInsights = useCallback(
    async (tokenIdx: number) => {
      dispatch({ type: 'SELECT_TOKEN_INDEX', payload: tokenIdx });
      dispatch({ type: 'SET_LOADING_INSIGHTS', payload: true });

      try {
        const res = await api.getMLInsights({
          source: state.source,
          language:
            state.language === 'auto' ? state.analysis?.language || 'python' : state.language,
          token_index: tokenIdx,
        });
        dispatch({ type: 'SET_ML_INSIGHTS', payload: res });
      } catch {
        dispatch({ type: 'SET_LOADING_INSIGHTS', payload: false });
      }
    },
    [dispatch, state.source, state.language, state.analysis]
  );

  return {
    runAnalysis,
    loadTokenInsights,
  };
}
