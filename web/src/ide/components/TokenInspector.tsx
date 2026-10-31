import React, { useEffect, useState } from 'react';
import { apiClient, type MLInsightsResponse } from '../../api/client';

export interface TokenItem {
  id: number;
  tokenId?: string;
  line: number;
  col: number;
  endLine?: number;
  endCol?: number;
  startOffset?: number;
  endOffset?: number;
  startOffsetCodepoint?: number;
  endOffsetCodepoint?: number;
  lexeme: string;
  displayLexeme?: string;
  type: string;
  category?: string;
  status: 'Valid' | 'Invalid';
  desc: string;
  diagnosticId?: string;
  severity?: string;
  evidence?: string[];
  ruleId?: string;
  suggestion?: string;
}

export function formatTokenLexeme(lexeme: string): { display: string; isSpecial: boolean; detail?: string } {
  if (!lexeme) return { display: '<empty>', isSpecial: true, detail: 'Empty sequence' };
  if (lexeme.includes('\uFEFF')) {
    return {
      display: '\\uFEFF',
      isSpecial: true,
      detail: 'U+FEFF (Zero Width No-Break Space / BOM)',
    };
  }
  if (lexeme === '\n') return { display: '\\n', isSpecial: true, detail: 'Newline' };
  if (lexeme === '\t') return { display: '\\t', isSpecial: true, detail: 'Tab' };
  if (lexeme === '\r') return { display: '\\r', isSpecial: true, detail: 'Carriage Return' };

  for (let i = 0; i < lexeme.length; i++) {
    const code = lexeme.charCodeAt(i);
    if (
      (code < 32 && code !== 9 && code !== 10 && code !== 13) ||
      (code >= 0x7F && code <= 0x9F) ||
      (code >= 0x200B && code <= 0x200F) ||
      (code >= 0x202A && code <= 0x202E) ||
      (code >= 0x2066 && code <= 0x2069)
    ) {
      return {
        display: `\\u${code.toString(16).toUpperCase().padStart(4, '0')}`,
        isSpecial: true,
        detail: `U+${code.toString(16).toUpperCase().padStart(4, '0')} (Invisible / Non-ASCII control codepoint)`,
      };
    }
  }
  return { display: lexeme, isSpecial: false };
}

interface TokenInspectorProps {
  token: TokenItem | null;
  activeSource?: string;
  activeLanguage?: string;
  onExplain: (token: TokenItem) => void;
  onFixWithModel?: (token: TokenItem) => void;
  onFixWithAi: (token: TokenItem) => void;
  onJumpToCode: (line: number, col: number, endLine?: number, endCol?: number) => void;
}

export const TokenInspector: React.FC<TokenInspectorProps> = ({
  token,
  activeSource,
  activeLanguage,
  onExplain,
  onFixWithModel,
  onFixWithAi,
  onJumpToCode,
}) => {
  const [mlInsights, setMlInsights] = useState<MLInsightsResponse | null>(null);
  const [loadingMl, setLoadingMl] = useState(false);

  useEffect(() => {
    let active = true;
    if (!token || !activeSource) {
      setMlInsights(null);
      return;
    }
    const tokenIdx = Math.max(0, token.id - 1);
    setLoadingMl(true);
    apiClient
      .getMLInsights({
        source: activeSource,
        language: activeLanguage,
        token_index: tokenIdx,
      })
      .then((res) => {
        if (active) setMlInsights(res);
      })
      .catch(() => {
        if (active) setMlInsights(null);
      })
      .finally(() => {
        if (active) setLoadingMl(false);
      });
    return () => {
      active = false;
    };
  }, [token?.id, activeSource, activeLanguage]);

  if (!token) {
    return (
      <div
        className="h-32 bg-surface-elevated border-t border-border-primary p-2.5 flex items-center justify-center shrink-0 shadow-xs transition-colors text-text-muted text-[11px]"
        id="tokenInspector"
      >
        Select a token from the table to inspect details and ML model assessment.
      </div>
    );
  }

  const isInvalid = token.status === 'Invalid';
  const lexemeInfo = formatTokenLexeme(token.lexeme);

  return (
    <div
      className="h-32 bg-surface-elevated border-t border-border-primary p-2.5 flex flex-col justify-between shrink-0 shadow-xs transition-colors"
      id="tokenInspector"
    >
      <div className="flex items-center justify-between border-b border-border-subtle pb-1">
        <div
          className={`flex items-center gap-1.5 font-semibold text-[12px] ${
            isInvalid ? 'text-status-error' : 'text-text-primary'
          }`}
          id="inspTitle"
        >
          <span className="material-symbols-outlined text-[16px]">
            {isInvalid ? 'report_problem' : 'check_circle'}
          </span>
          <span id="inspHeading">
            Token #{token.id} (Line {token.line}, Col {token.col}
            {token.endLine && token.endCol ? ` to Ln ${token.endLine}, Col ${token.endCol}` : ''})
          </span>
        </div>
        <div className="flex items-center gap-2">
          {mlInsights && mlInsights.ml_mode === 'on' && (
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase flex items-center gap-1 border ${
                mlInsights.predicted_label === 'MALICIOUS'
                  ? 'bg-status-error/15 text-status-error border-status-error/30'
                  : mlInsights.predicted_label === 'SUSPICIOUS'
                  ? 'bg-status-warning/15 text-status-warning border-status-warning/30'
                  : 'bg-status-success/15 text-status-success border-status-success/30'
              }`}
              title={`ML Model Classification: ${mlInsights.predicted_label || 'SAFE'} (Safe: ${((mlInsights.probabilities?.SAFE ?? 0) * 100).toFixed(0)}%, Susp: ${((mlInsights.probabilities?.SUSPICIOUS ?? 0) * 100).toFixed(0)}%, Mal: ${((mlInsights.probabilities?.MALICIOUS ?? 0) * 100).toFixed(0)}%)`}
            >
              <span className="material-symbols-outlined text-[11px]">memory</span>
              ML: {mlInsights.predicted_label || 'SAFE'}
            </span>
          )}
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
              isInvalid
                ? 'bg-status-error/15 text-status-error border border-status-error/40'
                : 'bg-status-success/15 text-status-success border border-status-success/40'
            }`}
            id="inspSeverity"
          >
            {isInvalid ? `Severity: ${token.severity || 'Error'}` : 'Status: Lexically Valid'}
          </span>
          <span className="text-[11px] text-text-muted font-mono" id="inspCwe">
            {token.ruleId || token.diagnosticId || (isInvalid ? 'Lexical Anomaly' : 'Standard Lexeme')}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 pt-1">
        <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-[11px]">
          <div>
            <span className="text-text-muted">Lexeme:</span>
            <span className="font-mono text-text-primary ml-1 font-semibold" id="inspLexeme">
              {lexemeInfo.display}
              {lexemeInfo.isSpecial && lexemeInfo.detail && (
                <span className="text-[11px] text-status-warning font-sans ml-1">
                  ({lexemeInfo.detail})
                </span>
              )}
            </span>
          </div>
          <div>
            <span className="text-text-muted">Status:</span>
            <span
              className={`font-mono font-bold ml-1 ${isInvalid ? 'text-status-error' : 'text-status-success'}`}
              id="inspStatus"
            >
              {token.status}
            </span>
          </div>
          <div>
            <span className="text-text-muted">Type:</span>
            <span className="font-mono text-text-secondary ml-1" id="inspType">
              {token.type} {token.category && token.category !== token.type ? `(${token.category})` : ''}
            </span>
          </div>
          <div>
            <span className="text-text-muted">ML Assessment:</span>
            <span className="font-mono text-text-secondary ml-1" id="inspML">
              {loadingMl ? (
                <span className="text-text-muted">Evaluating features...</span>
              ) : mlInsights?.probabilities ? (
                <span>
                  Safe {((mlInsights.probabilities.SAFE ?? 0) * 100).toFixed(0)}% · Mal{' '}
                  {((mlInsights.probabilities.MALICIOUS ?? 0) * 100).toFixed(0)}%
                </span>
              ) : (
                <span>Standing by</span>
              )}
            </span>
          </div>
          <div className="col-span-2 truncate flex items-center">
            <span className="text-text-muted shrink-0">Diagnostic / Description:</span>
            <span
              className={`font-mono ml-1 font-medium truncate ${isInvalid ? 'text-status-error' : 'text-text-secondary'}`}
              id="inspDiag"
              title={token.desc}
            >
              {token.desc}
            </span>
            {token.suggestion && (
              <span
                className="text-[11px] text-accent-fix font-sans ml-2 shrink-0 bg-accent-fix/10 px-1 rounded border border-accent-fix/30"
                title={token.suggestion}
              >
                Remediation: {token.suggestion}
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-1 w-36 shrink-0">
          <div className="flex items-center gap-1">
            <button
              type="button"
              className="flex-1 py-0.5 px-1.5 bg-surface-container hover:bg-surface-hover text-primary border border-primary/40 rounded text-[10px] font-semibold transition-colors focus-visible:ring-1 focus-visible:ring-primary"
              onClick={() => onExplain(token)}
            >
              Explain
            </button>
            <button
              type="button"
              className="flex-1 py-0.5 px-1.5 bg-surface-container hover:bg-surface-hover text-text-secondary border border-border-primary rounded text-[10px] transition-colors focus-visible:ring-1 focus-visible:ring-primary"
              onClick={() => onJumpToCode(token.line, token.col, token.endLine, token.endCol)}
            >
              Jump
            </button>
          </div>
          {(isInvalid || Boolean(token.diagnosticId)) && (
            <div className="flex items-center gap-1">
              {onFixWithModel && (
                <button
                  type="button"
                  className="flex-1 py-1 px-1 bg-primary/15 hover:bg-primary/25 text-primary border border-primary/40 rounded text-[10px] font-semibold transition-colors flex items-center justify-center gap-0.5"
                  onClick={() => onFixWithModel(token)}
                  title="Fix with deterministic Model & compiler rules"
                >
                  <span className="material-symbols-outlined text-[12px]">memory</span>
                  Model Fix
                </button>
              )}
              <button
                type="button"
                className="flex-1 py-1 px-1 bg-accent-fix/15 hover:bg-accent-fix/25 text-accent-fix border border-accent-fix/40 rounded text-[10px] font-semibold transition-colors flex items-center justify-center gap-0.5"
                onClick={() => onFixWithAi(token)}
                title="Synthesize fix with AI Assistant"
              >
                <span className="material-symbols-outlined text-[12px]">auto_fix_high</span>
                AI Fix
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

