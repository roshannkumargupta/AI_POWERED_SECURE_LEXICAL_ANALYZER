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
  hasAnalyzed?: boolean;
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
  hasAnalyzed = true,
  errorMessage = null,
}) => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortField, setSortField] = useState<'position' | 'line' | 'col' | 'index'>('position');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [pageSize, setPageSize] = useState<number | 'ALL'>(100);
  const [currentPage, setCurrentPage] = useState(1);

  // Dynamic token types from actual backend results
  const availableTypes = useMemo(() => {
    const set = new Set<string>();
    tokens.forEach((t) => {
      if (t.type) set.add(t.type);
    });
    return Array.from(set).sort();
  }, [tokens]);

  // Dynamic categories from actual backend results
  const availableCategories = useMemo(() => {
    const set = new Set<string>();
    tokens.forEach((t) => {
      if (t.category) set.add(t.category);
    });
    return Array.from(set).sort();
  }, [tokens]);

  const handleHeaderSort = (field: 'line' | 'col' | 'index') => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredTokens = useMemo(() => {
    const q = search.toLowerCase().trim();
    const result = tokens.filter((t) => {
      const matchQ =
        !q ||
        t.lexeme.toLowerCase().includes(q) ||
        t.type.toLowerCase().includes(q) ||
        (t.category && t.category.toLowerCase().includes(q)) ||
        t.desc.toLowerCase().includes(q) ||
        String(t.line).includes(q) ||
        String(t.col).includes(q);
      const matchType = typeFilter === 'ALL' || t.type.toLowerCase() === typeFilter.toLowerCase();
      const matchCategory =
        categoryFilter === 'ALL' ||
        (t.category && t.category.toLowerCase() === categoryFilter.toLowerCase());
      const matchStatus =
        statusFilter === 'ALL' || t.status.toLowerCase() === statusFilter.toLowerCase();
      return matchQ && matchType && matchCategory && matchStatus;
    });

    return result.sort((a, b) => {
      let cmp = 0;
      if (sortField === 'line') {
        cmp = a.line !== b.line ? a.line - b.line : a.col - b.col;
      } else if (sortField === 'col') {
        cmp = a.col !== b.col ? a.col - b.col : a.line - b.line;
      } else if (sortField === 'index') {
        cmp = a.id - b.id;
      } else {
        cmp = a.line !== b.line ? a.line - b.line : a.col - b.col;
      }
      return sortDirection === 'asc' ? cmp : -cmp;
    });
  }, [tokens, search, typeFilter, categoryFilter, statusFilter, sortField, sortDirection]);

  const validCount = useMemo(() => tokens.filter((t) => t.status === 'Valid').length, [tokens]);
  const invalidCount = useMemo(() => tokens.filter((t) => t.status === 'Invalid').length, [tokens]);

  const totalPages = pageSize === 'ALL' ? 1 : Math.max(1, Math.ceil(filteredTokens.length / pageSize));

  // Reset to page 1 if current page is out of bounds
  React.useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(1);
    }
  }, [totalPages, currentPage]);

  // Auto-page when a token is selected
  React.useEffect(() => {
    if (selectedTokenId !== null && pageSize !== 'ALL') {
      const idx = filteredTokens.findIndex((t) => t.id === selectedTokenId);
      if (idx !== -1) {
        const targetPage = Math.floor(idx / pageSize) + 1;
        if (targetPage !== currentPage) {
          setCurrentPage(targetPage);
        }
      }
    }
  }, [selectedTokenId, filteredTokens, pageSize, currentPage]);

  const paginatedTokens = useMemo(() => {
    if (pageSize === 'ALL') return filteredTokens;
    const start = (currentPage - 1) * pageSize;
    return filteredTokens.slice(start, start + pageSize);
  }, [filteredTokens, currentPage, pageSize]);

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

          {/* Dynamic Category Filter */}
          <select
            className="bg-surface-deepest text-text-secondary text-[11px] border border-border-primary rounded px-2 py-0.5 outline-none max-w-[120px] truncate"
            id="tokenCategoryFilter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="ALL">All Categories</option>
            {availableCategories.map((c) => (
              <option key={c} value={c}>
                {c} ({tokens.filter((tok) => tok.category === c).length})
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
            title={`Sort direction: ${sortDirection === 'asc' ? 'Ascending' : 'Descending'}`}
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
          <thead className="bg-surface-deepest sticky top-0 border-b border-border-primary text-text-secondary text-[11px] uppercase font-bold tracking-wider z-10">
            <tr>
              <th
                className="py-1.5 px-3 w-16 text-center cursor-pointer hover:text-text-primary"
                onClick={() => handleHeaderSort('index')}
                title="Sort by index"
              >
                # {sortField === 'index' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
              </th>
              <th
                className="py-1.5 px-3 w-16 cursor-pointer hover:text-text-primary"
                onClick={() => handleHeaderSort('line')}
                title="Sort by line"
              >
                Line {sortField === 'line' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
              </th>
              <th
                className="py-1.5 px-3 w-16 cursor-pointer hover:text-text-primary"
                onClick={() => handleHeaderSort('col')}
                title="Sort by column"
              >
                Col {sortField === 'col' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
              </th>
              <th className="py-1.5 px-3">Lexeme</th>
              <th className="py-1.5 px-3">Type</th>
              <th className="py-1.5 px-3 w-28">Status</th>
              <th className="py-1.5 px-3">Description / Diagnostic</th>
              <th className="py-1.5 px-2 w-10 text-center">Nav</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle font-mono text-[11px]" id="tokenTableBody">
            {filteredTokens.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-text-muted font-sans text-[12px]">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <span className="material-symbols-outlined text-[28px] text-text-muted/50">
                      {isAnalyzing
                        ? 'sync'
                        : errorMessage
                        ? 'error'
                        : !hasAnalyzed
                        ? 'code_blocks'
                        : 'search_off'}
                    </span>
                    <div className="font-medium text-text-secondary">
                      {isAnalyzing
                        ? 'Performing lexical scan on active document...'
                        : errorMessage
                        ? `Analysis failed: ${errorMessage}`
                        : !hasAnalyzed
                        ? 'Document not analyzed yet. Press Analyze (⌘↵) to run the lexical analyzer.'
                        : tokens.length === 0
                        ? 'Document is empty or produced zero tokens.'
                        : 'No tokens match current search and filters.'}
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedTokens.map((t) => {
                const isInvalid = t.status === 'Invalid';
                const isSelected = t.id === selectedTokenId;
                const formatted = formatTokenLexeme(t.lexeme);

                let rowClass = 'group token-row hover:bg-surface-hover cursor-pointer transition-colors';
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
                    onClick={() => onSelectToken(t)}
                    onDoubleClick={() => onJumpToCode?.(t.line, t.col, t.endLine, t.endCol)}
                  >
                    <td className="py-1.5 px-3 text-center text-text-muted font-normal">#{t.id}</td>
                    <td className="py-1.5 px-3">Ln {t.line}</td>
                    <td className="py-1.5 px-3">Col {t.col}</td>
                    <td className="py-1.5 px-3 font-medium truncate max-w-[260px]">
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
                      <span className="px-2 py-0.5 rounded bg-surface-container border border-border-subtle text-[11px] font-mono">
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
                    <td className="py-1.5 px-2 text-center" onClick={(e) => e.stopPropagation()}>
                      <button
                        type="button"
                        className="opacity-0 group-hover:opacity-100 p-0.5 text-text-muted hover:text-primary rounded transition-opacity"
                        title="Jump to code in editor"
                        onClick={() => {
                          onSelectToken(t);
                          onJumpToCode?.(t.line, t.col, t.endLine, t.endCol);
                        }}
                      >
                        <span className="material-symbols-outlined text-[13px]">my_location</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls for Large Codebases */}
      {filteredTokens.length > 0 && (
        <div className="h-7 px-3 bg-surface-deepest border-t border-border-subtle flex items-center justify-between shrink-0 text-[11px] text-text-muted font-mono select-none">
          <div className="flex items-center gap-2">
            <span>
              Showing{' '}
              {pageSize === 'ALL'
                ? `all ${filteredTokens.length}`
                : `${(currentPage - 1) * pageSize + 1}–${Math.min(currentPage * pageSize, filteredTokens.length)} of ${filteredTokens.length}`}{' '}
              tokens
            </span>
          </div>

          <div className="flex items-center gap-2">
            {pageSize !== 'ALL' && totalPages > 1 && (
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  className="px-1.5 py-0.5 rounded hover:bg-surface-hover hover:text-text-primary disabled:opacity-30 disabled:pointer-events-none"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage(1)}
                  title="First page"
                >
                  «
                </button>
                <button
                  type="button"
                  className="px-1.5 py-0.5 rounded hover:bg-surface-hover hover:text-text-primary disabled:opacity-30 disabled:pointer-events-none"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  title="Previous page"
                >
                  ‹
                </button>
                <span className="px-1 text-text-secondary">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  className="px-1.5 py-0.5 rounded hover:bg-surface-hover hover:text-text-primary disabled:opacity-30 disabled:pointer-events-none"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  title="Next page"
                >
                  ›
                </button>
                <button
                  type="button"
                  className="px-1.5 py-0.5 rounded hover:bg-surface-hover hover:text-text-primary disabled:opacity-30 disabled:pointer-events-none"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage(totalPages)}
                  title="Last page"
                >
                  »
                </button>
              </div>
            )}

            <div className="flex items-center gap-1 ml-2">
              <span className="text-[10px]">Show:</span>
              <select
                className="bg-surface-container text-text-secondary text-[10px] border border-border-subtle rounded px-1 py-0.2 outline-none font-sans"
                value={pageSize}
                onChange={(e) => {
                  const val = e.target.value === 'ALL' ? 'ALL' : Number(e.target.value);
                  setPageSize(val);
                  setCurrentPage(1);
                }}
              >
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={250}>250</option>
                <option value="ALL">All</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
