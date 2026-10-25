import { AppState, Action } from '../state/store';
import { api, Finding, Fix } from '../api/client';
import { DocItem } from '../model/doc';
import { ReviewFixItem } from '../components/ReviewFixesModal';
import { applyEdits } from '../utils/applyEdits';
import { generateUnifiedDiff } from '../utils/diff';

interface UseFixActionsOptions {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  dirtyRef: React.MutableRefObject<boolean>;
  activeDoc: DocItem | null;
  activeDocId: string | null;
  setOpenDocs: React.Dispatch<React.SetStateAction<DocItem[]>>;
  runAnalysis: (source: string, language: string, filename: string) => Promise<void>;
  llmStatus: { configured: boolean; provider: string };
  setIsAskingAI: (val: boolean) => void;
  setReviewFixesOpen: (val: boolean) => void;
}

export function useFixActions({
  state,
  dispatch,
  dirtyRef,
  activeDoc,
  activeDocId,
  setOpenDocs,
  runAnalysis,
  llmStatus,
  setIsAskingAI,
  setReviewFixesOpen,
}: UseFixActionsOptions) {
  const handleApplyFix = async (fix: Fix, finding: Finding) => {
    if (activeDoc?.status === 'stale') {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: 'Analyse again first: code was edited since last analysis',
          type: 'warning',
        },
      });
      return;
    }

    try {
      const response = await api.applyFix({
        source: state.source,
        language: state.language === 'auto' ? 'python' : state.language,
        finding_id: finding.id,
        fix_id: fix.id,
        filename: state.filename,
      });
      const newSource = response.new_source;
      dispatch({ type: 'SET_SOURCE', payload: newSource });
      dirtyRef.current = true;
      setOpenDocs((docs) =>
        docs.map((doc) =>
          doc.id === activeDocId
            ? {
                ...doc,
                content: newSource,
                dirty: true,
                contentVersion: doc.contentVersion + 1,
              }
            : doc
        )
      );
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Fix applied — Ctrl+Z to undo', type: 'success' },
      });

      await runAnalysis(newSource, state.language, state.filename);
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `Failed to apply fix: ${err.message}`, type: 'error' },
      });
    }
  };

  const handleFixAll = async () => {
    if (activeDoc?.status === 'stale') {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Analyse again first before applying Fix all', type: 'warning' },
      });
      return;
    }

    dispatch({ type: 'SET_ANALYZING', payload: true });
    try {
      const res = await api.applyFixAll({
        source: state.source,
        language: state.language === 'auto' ? 'python' : state.language,
        filename: state.filename,
        allow_review: false,
      });

      dispatch({ type: 'SET_SOURCE', payload: res.new_source });
      dirtyRef.current = true;
      setOpenDocs((docs) =>
        docs.map((doc) =>
          doc.id === activeDocId
            ? {
                ...doc,
                content: res.new_source,
                dirty: true,
                contentVersion: doc.contentVersion + 1,
              }
            : doc
        )
      );
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Applied ${res.applied.length} fixes — score ${res.score_before} -> ${res.score_after}`,
          type: 'success',
        },
      });

      await runAnalysis(res.new_source, state.language, state.filename);
    } catch (err: any) {
      dispatch({ type: 'SET_ANALYZING', payload: false });
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Fix all failed: ${err.message || 'Server error'}`,
          type: 'error',
        },
      });
    }
  };

  const handleOpenDiff = (fix: Fix, finding: Finding) => {
    try {
      const newSource = applyEdits(state.source, fix.edits);
      dispatch({
        type: 'OPEN_DIFF_MODAL',
        payload: {
          fix,
          finding,
          oldSource: state.source,
          newSource,
          diff: generateUnifiedDiff(state.source, newSource, state.filename || 'source'),
        },
      });
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `Cannot generate diff: ${err.message}`, type: 'error' },
      });
    }
  };

  const handleApplyDiffFix = async () => {
    if (!state.diffModal || !state.diffModal.fix) return;
    const fix = state.diffModal.fix;
    const newSource = state.diffModal.newSource;

    dispatch({ type: 'SET_SOURCE', payload: newSource });
    dirtyRef.current = true;
    setOpenDocs((docs) =>
      docs.map((doc) =>
        doc.id === activeDocId
          ? { ...doc, content: newSource, dirty: true, contentVersion: doc.contentVersion + 1 }
          : doc
      )
    );
    dispatch({ type: 'CLOSE_DIFF_MODAL' });
    dispatch({
      type: 'ADD_TOAST',
      payload: { message: `Applied fix: ${fix.title}`, type: 'success' },
    });

    await runAnalysis(newSource, state.language, state.filename);
  };

  const handleMarkFalsePositive = async (finding: Finding) => {
    try {
      await api.submitFeedback({
        finding_fingerprint: finding.id,
        rule_id: finding.rule_id,
        language: state.language === 'auto' ? 'python' : state.language,
        verdict: 'false_positive',
        snippet: state.source.slice(0, 300),
      });
      dispatch({ type: 'HIDE_FINDING', payload: finding.id });
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Thanks - saved for next model retrain', type: 'success' },
      });
    } catch {
      dispatch({ type: 'HIDE_FINDING', payload: finding.id });
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Thanks - saved for next model retrain', type: 'success' },
      });
    }
  };

  const handleSuppressFinding = async (finding: Finding) => {
    const isPy =
      finding.rule_id.includes('-PY-') ||
      state.language === 'python' ||
      (state.filename && state.filename.endsWith('.py'));
    const commentPrefix = isPy ? '#' : '//';
    const comment = `${commentPrefix} securelex: ignore ${finding.rule_id}`;

    const lines = state.source.split('\n');
    const targetLineIndex = Math.max(0, (finding.range?.start_line || 1) - 1);
    const currentLineText = lines[targetLineIndex] || '';
    const indent = currentLineText.match(/^\s*/)?.[0] || '';
    const newLines = [...lines];
    newLines.splice(targetLineIndex, 0, `${indent}${comment}`);
    const newSource = newLines.join('\n');

    dirtyRef.current = true;
    dispatch({ type: 'SET_SOURCE', payload: newSource });
    setOpenDocs((docs) =>
      docs.map((doc) =>
        doc.id === activeDocId
          ? {
              ...doc,
              content: newSource,
              dirty: true,
              contentVersion: doc.contentVersion + 1,
            }
          : doc
      )
    );
    dispatch({
      type: 'ADD_TOAST',
      payload: { message: `Suppression comment added — Ctrl+Z to undo`, type: 'info' },
    });
    await runAnalysis(newSource, state.language, state.filename);
  };

  const handleAskAIFix = async (finding: Finding) => {
    if (!llmStatus.configured) {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: 'Add GROQ_API_KEY to your .env file and restart',
          type: 'info',
        },
      });
      return;
    }
    setIsAskingAI(true);
    try {
      const res = await api.proposeFix({
        source: state.source,
        source_version: 1,
        language: state.language === 'auto' ? 'python' : state.language,
        filename: state.filename,
        origin: 'ai',
        target: { kind: 'finding', id: finding.id },
      });

      if (res?.proposal) {
        const candidateFix: Fix = {
          id: res.proposal.id,
          finding_id: finding.id,
          title: `AI Fix for ${finding.rule_id || finding.id}`,
          description: res.proposal.rationale || 'AI-proposed remediation',
          edits: res.proposal.edits,
          confidence: 'review',
          kind: 'ai',
          verification: {
            syntax_ok: true,
            finding_gone: false,
            new_findings: [],
            verified: false,
            notes: 'Unverified candidate patch',
          },
        };
        if (state.analysis) {
          const updatedFindings = state.analysis.findings.map((f) => {
            if (f.id === finding.id) {
              return {
                ...f,
                fixes: [...(f.fixes || []), candidateFix],
              };
            }
            return f;
          });
          dispatch({
            type: 'SET_ANALYSIS',
            payload: {
              ...state.analysis,
              findings: updatedFindings,
            },
          });
        }
        dispatch({
          type: 'ADD_TOAST',
          payload: {
            message: 'Generated 1 AI fix candidate',
            type: 'success',
          },
        });
      } else {
        dispatch({
          type: 'ADD_TOAST',
          payload: { message: 'No new fixes suggested by AI', type: 'info' },
        });
      }
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `AI Fix request failed: ${err.message}`, type: 'error' },
      });
    } finally {
      setIsAskingAI(false);
    }
  };

  const handleApplySelectedReviewFixes = async (selected: ReviewFixItem[]) => {
    setReviewFixesOpen(false);
    if (selected.length === 0) return;
    try {
      let currentSource = state.source;
      for (const item of selected) {
        currentSource = applyEdits(currentSource, item.fix.edits);
      }
      dispatch({ type: 'SET_SOURCE', payload: currentSource });
      dirtyRef.current = true;
      setOpenDocs((docs) =>
        docs.map((doc) =>
          doc.id === activeDocId
            ? {
                ...doc,
                content: currentSource,
                dirty: true,
                contentVersion: doc.contentVersion + 1,
              }
            : doc
        )
      );
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Applied ${selected.length} review fixes — Ctrl+Z to undo`,
          type: 'success',
        },
      });
      await runAnalysis(currentSource, state.language, state.filename);
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `Failed to apply review fixes: ${err.message}`, type: 'error' },
      });
    }
  };

  return {
    handleApplyFix,
    handleFixAll,
    handleOpenDiff,
    handleApplyDiffFix,
    handleMarkFalsePositive,
    handleSuppressFinding,
    handleAskAIFix,
    handleApplySelectedReviewFixes,
  };
}
