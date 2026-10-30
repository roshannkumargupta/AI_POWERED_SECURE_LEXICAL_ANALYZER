import React from 'react';

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
  onExplain: (token: TokenItem) => void;
  onFixWithAi: (token: TokenItem) => void;
  onJumpToCode: (line: number, col: number, endLine?: number, endCol?: number) => void;
}

export const TokenInspector: React.FC<TokenInspectorProps> = ({
  token,
  onExplain,
  onFixWithAi,
  onJumpToCode,
}) => {
  if (!token) {
    return (
      <div
        className="h-28 bg-surface-elevated border-t border-border-primary p-2.5 flex items-center justify-center shrink-0 shadow-xs transition-colors text-text-muted text-[11px]"
        id="tokenInspector"
      >
        Select a token from the table to inspect details.
      </div>
    );
  }

  const isInvalid = token.status === 'Invalid';
  const lexemeInfo = formatTokenLexeme(token.lexeme);

  return (
    <div
      className="h-28 bg-surface-elevated border-t border-border-primary p-2.5 flex flex-col justify-between shrink-0 shadow-xs transition-colors"
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
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
              isInvalid
                ? 'bg-status-error/15 text-status-error border border-status-error/40'
                : 'bg-status-success/15 text-status-success border border-status-success/40'
            }`}
            id="inspSeverity"
          >
            {isInvalid ? `Severity: ${token.severity || 'Error'}` : 'Status: Lexically Valid'}
          </span>
          <span className="text-[10px] text-text-muted font-mono" id="inspCwe">
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
                <span className="text-[10px] text-status-warning font-sans ml-1">
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
            <span className="text-text-muted">Offsets:</span>
            <span className="font-mono text-text-secondary ml-1" id="inspOffsets">
              {token.startOffset !== undefined ? `UTF-16: ${token.startOffset}..${token.endOffset}` : 'N/A'}
              {token.startOffsetCodepoint !== undefined ? ` (Codepoint: ${token.startOffsetCodepoint}..${token.endOffsetCodepoint})` : ''}
            </span>
          </div>
          <div className="col-span-2 truncate">
            <span className="text-text-muted">Diagnostic / Description:</span>
            <span
              className={`font-mono ml-1 font-medium ${isInvalid ? 'text-status-error' : 'text-text-secondary'}`}
              id="inspDiag"
              title={token.desc}
            >
              {token.desc}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-1 w-32 shrink-0">
          <button
            type="button"
            className="w-full py-0.5 px-2 bg-surface-container hover:bg-surface-hover text-primary border border-primary/40 rounded text-[10px] font-semibold transition-colors"
            onClick={() => onExplain(token)}
          >
            Explain
          </button>
          {(isInvalid || Boolean(token.diagnosticId)) && (
            <button
              type="button"
              className="w-full py-0.5 px-2 bg-accent-fix/15 hover:bg-accent-fix/25 text-accent-fix border border-accent-fix/40 rounded text-[10px] font-semibold transition-colors"
              onClick={() => onFixWithAi(token)}
            >
              Fix with AI
            </button>
          )}
          <button
            type="button"
            className="w-full py-0.5 px-2 bg-surface-container hover:bg-surface-hover text-text-secondary border border-border-primary rounded text-[10px] transition-colors"
            onClick={() => onJumpToCode(token.line, token.col, token.endLine, token.endCol)}
          >
            Jump to Code
          </button>
        </div>
      </div>
    </div>
  );
};

