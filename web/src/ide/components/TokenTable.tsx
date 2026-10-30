import React, { useState, useMemo } from 'react';
import { type TokenItem, formatTokenLexeme } from './TokenInspector';

interface TokenTableProps {
  tokens: TokenItem[];
  selectedTokenId: number | null;
  onSelectToken: (token: TokenItem) => void;
  onJumpToCode?: (line: number, col: number, endLine?: number, endCol?: number) => void;
  languageStandard?: string;
  isAnalyzing?: boolean;
  isStale?: boolean;
  errorMessage?: string | null;
}

export const TokenTable: React.FC<TokenTableProps> = ({
  tokens,
  selectedTokenId,
  onSelectToken,
  onJumpToCode,
  languageStandard = 'ISO/IEC 14882:2020 C++',
  isAnalyzing = false,
  isStale = false,
  errorMessage = null,
}) => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Dynamic token types from actual backend results
  const availableTypes = useMemo(() => {
    const set = new Set<string>();
    tokens.forEach((t) => {
      if (t.type) set.add(t.type);
    });
    return Array.from(set).sort();
  }, [tokens]);

  const filteredTokens = useMemo(() => {
    const q = search.toLowerCase().trim();
    const result = tokens.filter((t) => {
      const matchQ =
        !q ||
        t.lexeme.toLowerCase().includes(q) ||
        t.type.toLowerCase().includes(q) ||
        t.desc.toLowerCase().includes(q) ||
        String(t.line).includes(q) ||
        String(t.col).includes(q);
      const matchType = typeFilter === 'ALL' || t.type.toLowerCase() === typeFilter.toLowerCase();
      const matchStatus =
        statusFilter === 'ALL' || t.status.toLowerCase() === statusFilter.toLowerCase();
      return matchQ && matchType && matchStatus;
    });

    return result.sort((a, b) => {
      if (a.line !== b.line) {
        return sortDirection === 'asc' ? a.line - b.line : b.line - a.line;
      }
      if (a.col !== b.col) {
        return sortDirection === 'asc' ? a.col - b.col : b.col - a.col;
      }
      return sortDirection === 'asc' ? a.id - b.id : b.id - a.id;
    });
  }, [tokens, search, typeFilter, statusFilter, sortDirection]);

  const validCount = useMemo(() => tokens.filter((t) => t.status === 'Valid').length, [tokens]);
  const invalidCount = useMemo(() => tokens.filter((t) => t.status === 'Invalid').length, [tokens]);

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden" id="view-tokens">
      {/* Top Filter & Status Bar */}
      <div className="h-9 px-3 bg-surface-explorer border-b border-border-subtle flex items-center justify-between shrink-0 gap-2 transition-colors">
        <div className="flex items-center gap-2 min-w-0 truncate">
          <span className="text-text-primary font-semibold text-[11px] shrink-0">
            Lexical Analysis
          </span>
          <span className="text-[10px] text-text-muted bg-surface-container px-1.5 py-0.5 rounded border border-border-subtle font-mono truncate hidden sm:inline">
            {languageStandard}
          </span>
          {isAnalyzing && (
            <span className="flex items-center gap-1 text-[10px] text-primary font-medium animate-pulse">
              <span className="material-symbols-outlined text-[13px] animate-spin">sync</span>
              <span>Scanning...</span>
            </span>
          )}
          {!isAnalyzing && isStale && (
            <span
              className="flex items-center gap-1 text-[10px] text-status-warning bg-status-warning/10 px-1.5 py-0.5 rounded border border-status-warning/30"
              title="Editor content changed since last analysis"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
              <span>Stale</span>
            </span>
          )}
          {!isAnalyzing && !errorMessage && tokens.length > 0 && (
            <span className="text-[10px] text-text-muted font-mono hidden md:inline">
              ({validCount} valid{invalidCount > 0 ? `, ${invalidCount} invalid` : ''})
            </span>
          )}
        </div>

        {/* Filters and Controls */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="relative flex items-center">
            <span className="material-symbols-outlined absolute left-2 text-[13px] text-text-muted">
              search
            </span>
            <input
              className="pl-7 pr-2 py-0.5 text-[11px] bg-surface-deepest text-text-primary border border-border-primary rounded focus:border-primary outline-none w-32 sm:w-44 placeholder-text-muted transition-all"
              id="tokenSearch"
              placeholder="Filter tokens..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* Dynamic Token Type Filter */}
          <select
            className="bg-surface-deepest text-text-secondary text-[11px] border border-border-primary rounded px-2 py-0.5 outline-none max-w-[120px] truncate"
            id="tokenTypeFilter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="ALL">All Types ({tokens.length})</option>
            {availableTypes.map((t) => (
              <option key={t} value={t}>
                {t} ({tokens.filter((tok) => tok.type === t).length})
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            className="bg-surface-deepest text-text-secondary text-[11px] border border-border-primary rounded px-2 py-0.5 outline-none"
            id="tokenStatusFilter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Status</option>
            <option value="Valid">Valid ({validCount})</option>
            <option value="Invalid">Invalid ({invalidCount})</option>
          </select>

          {/* Sort Position Toggle */}
          <button
            type="button"
            className="p-1 hover:text-text-primary text-text-muted hover:bg-surface-hover rounded transition-colors"
            onClick={() => setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))}
            title={`Sort source position: ${sortDirection === 'asc' ? 'Ascending' : 'Descending'}`}
          >
            <span className="material-symbols-outlined text-[14px]">
              {sortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward'}
            </span>
          </button>
        </div>
      </div>

      {/* Backend API Error Banner (Separated from lexical errors) */}
      {errorMessage && (
        <div className="px-3 py-2 bg-status-error/15 border-b border-status-error/30 text-status-error text-[11px] flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px]">error</span>
            <span>{errorMessage}</span>
          </div>
          <span className="text-[10px] text-text-muted font-mono">Backend API status: Error</span>
        </div>
      )}

      {/* Token Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-left border-collapse text-[11px] select-none">
          <thead className="bg-surface-deepest sticky top-0 border-b border-border-primary text-text-secondary text-[10px] uppercase font-bold z-10">
            <tr>
              <th
                className="py-1.5 px-3 w-12 text-center cursor-pointer hover:text-text-primary"
                onClick={() => setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))}
                title="Sort by index"
              >
                # {sortDirection === 'asc' ? '↑' : '↓'}
              </th>
              <th
                className="py-1.5 px-3 w-16 cursor-pointer hover:text-text-primary"
                onClick={() => setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))}
                title="Sort by line"
              >
                Line
              </th>
              <th
                className="py-1.5 px-3 w-16 cursor-pointer hover:text-text-primary"
                onClick={() => setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'))}
                title="Sort by column"
              >
                Col
              </th>
              <th className="py-1.5 px-3">Lexeme</th>
              <th className="py-1.5 px-3">Type</th>
              <th className="py-1.5 px-3 w-28">Status</th>
              <th className="py-1.5 px-3">Description / Diagnostic</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle font-mono text-[11px]" id="tokenTableBody">
            {filteredTokens.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-text-muted font-sans text-[12px]">
                  {isAnalyzing
                    ? 'Performing lexical scan on active document...'
                    : tokens.length === 0
                    ? 'No tokens available. Press Analyze (⌘↵) to run the lexical analyzer.'
                    : 'No tokens match current search and filters.'}
                </td>
              </tr>
            ) : (
              filteredTokens.map((t) => {
                const isInvalid = t.status === 'Invalid';
                const isSelected = t.id === selectedTokenId;
                const formatted = formatTokenLexeme(t.lexeme);

                let rowClass = 'token-row hover:bg-surface-hover cursor-pointer transition-colors';
                if (isInvalid) {
                  rowClass +=
                    ' bg-status-error/10 border-l-2 border-status-error text-status-error font-semibold';
                } else if (isSelected) {
                  rowClass += ' bg-surface-selected text-text-primary font-medium';
                }

                return (
                  <tr
                    key={t.id}
                    className={rowClass}
                    onClick={() => {
                      onSelectToken(t);
                      onJumpToCode?.(t.line, t.col, t.endLine, t.endCol);
                    }}
                  >
                    <td className="py-1.5 px-3 text-center text-text-muted font-normal">#{t.id}</td>
                    <td className="py-1.5 px-3">Ln {t.line}</td>
                    <td className="py-1.5 px-3">Col {t.col}</td>
                    <td className="py-1.5 px-3 font-medium truncate max-w-[220px]">
                      <span
                        className={
                          formatted.isSpecial ? 'bg-status-warning/20 text-status-warning px-1 rounded' : ''
                        }
                        title={formatted.detail || t.lexeme}
                      >
                        {formatted.display}
                      </span>
                    </td>
                    <td className="py-1.5 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-surface-container border border-border-subtle text-[10px]">
                        {t.type}
                      </span>
                    </td>
                    <td className="py-1.5 px-3">
                      <span
                        className={`inline-flex items-center gap-1 font-semibold ${
                          isInvalid ? 'text-status-error' : 'text-status-success'
                        }`}
                      >
                        <span className="material-symbols-outlined text-[13px]">
                          {isInvalid ? 'cancel' : 'check_circle'}
                        </span>
                        <span>{t.status}</span>
                      </span>
                    </td>
                    <td
                      className="py-1.5 px-3 text-text-muted font-sans text-[11px] truncate max-w-[340px]"
                      title={t.desc}
                    >
                      {t.desc}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
