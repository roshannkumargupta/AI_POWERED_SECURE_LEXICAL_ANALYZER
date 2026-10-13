import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { AnalysisResultV2, TokenV2 } from '../../api/client';
import { categoryGroup, filterAndSortTokens, isAnalysisIncomplete, tokenCounts, tokenCsv, tokenJson, tokenSecurityFindings, tokenTsv, visibleLexeme, type TokenFilter, type TokenSort } from './tokenModel';
import { explainToken } from './explanations';
import './tokens.css';

interface TokensPanelProps {
  result: AnalysisResultV2 | null;
  analysisStatus: 'idle' | 'running' | 'ok' | 'stale' | 'error';
  currentVersion: number | null;
  language: string;
  grammarLabel: string;
  selectedTokenId: string | null;
  inspectorOpen: boolean;
  onSelect(token: TokenV2): void;
  onFix?(token: TokenV2): void;
  fixEnabled?: boolean;
  onToggleInspector(): void;
  onExport(message: string, error?: boolean): void;
}

const ROW_HEIGHT = 30;
const OVERSCAN = 8;

function positionLabel(token: TokenV2) {
  return token.start_line === token.end_line
    ? `${token.start_line}:${token.start_column}–${token.end_column}`
    : `${token.start_line}:${token.start_column}–${token.end_line}:${token.end_column}`;
}

export function TokensPanel({ result, analysisStatus, currentVersion, language, grammarLabel, selectedTokenId, inspectorOpen, onSelect, onFix, fixEnabled = false, onToggleInspector, onExport }: TokensPanelProps) {
  const [filter, setFilter] = useState<TokenFilter>('All');
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<TokenSort>('position');
  const [scrollTop, setScrollTop] = useState(0);
  const [viewportHeight, setViewportHeight] = useState(300);
  const scrollRef = useRef<HTMLDivElement>(null);
  const counts = useMemo(() => tokenCounts(result?.tokens ?? []), [result]);
  const visible = useMemo(() => filterAndSortTokens(result?.tokens ?? [], filter, search, sort), [result, filter, search, sort]);
  const selected = result?.tokens.find((token) => token.id === selectedTokenId) ?? null;
  const status = analysisStatus === 'stale' || (result && currentVersion !== null && result.source_version !== currentVersion)
    ? 'Stale'
    : analysisStatus === 'ok' && isAnalysisIncomplete(result) ? 'Analysis incomplete'
      : analysisStatus === 'ok' && result ? 'Up to date'
        : analysisStatus === 'running' ? 'Analysis running'
          : analysisStatus === 'error' ? 'Analysis error' : 'Not analysed';
  const categories = [...counts.categories.entries()].sort(([a], [b]) => {
    const order = ['Keywords', 'Identifiers', 'Operators', 'Literals', 'Delimiters', 'Comments', 'Preprocessor'];
    return (order.indexOf(a) === -1 ? order.length : order.indexOf(a)) - (order.indexOf(b) === -1 ? order.length : order.indexOf(b)) || a.localeCompare(b);
  });
  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const count = Math.ceil(viewportHeight / ROW_HEIGHT) + OVERSCAN * 2;
  const rows = visible.slice(start, start + count);

  useLayoutEffect(() => {
    const element = scrollRef.current;
    if (!element) return;
    const update = () => setViewportHeight(element.clientHeight);
    update();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const chooseAt = (index: number) => {
    const token = visible[index];
    if (!token) return;
    const rowTop = index * ROW_HEIGHT;
    const scroller = scrollRef.current;
    if (scroller && (rowTop < scroller.scrollTop || rowTop + ROW_HEIGHT > scroller.scrollTop + scroller.clientHeight)) {
      scroller.scrollTop = Math.max(0, rowTop - ROW_HEIGHT * 2);
      setScrollTop(scroller.scrollTop);
    }
    onSelect(token);
  };
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!visible.length) return;
    const currentIndex = visible.findIndex((token) => token.id === selectedTokenId);
    if (event.key === 'ArrowDown') { event.preventDefault(); chooseAt(Math.min(visible.length - 1, currentIndex < 0 ? 0 : currentIndex + 1)); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); chooseAt(Math.max(0, currentIndex < 0 ? 0 : currentIndex - 1)); }
    else if (event.key === 'Home') { event.preventDefault(); chooseAt(0); }
    else if (event.key === 'End') { event.preventDefault(); chooseAt(visible.length - 1); }
    else if (event.key === 'Enter') { event.preventDefault(); chooseAt(currentIndex < 0 ? 0 : currentIndex); }
  };

  const copy = async () => {
    try { await navigator.clipboard.writeText(tokenTsv(visible)); onExport('Current tokens copied as TSV.'); }
    catch { onExport('Clipboard access is unavailable in this browser.', true); }
  };
  const download = (format: 'csv' | 'json') => {
    if (!result) return;
    const payload = format === 'csv' ? tokenCsv(visible) : tokenJson(result, visible);
    const blob = new Blob([payload], { type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = window.document.createElement('a');
    anchor.href = url;
    anchor.download = format === 'csv' ? 'tokens.csv' : 'tokens.json';
    anchor.click();
    URL.revokeObjectURL(url);
    onExport(`Current tokens exported as ${format.toUpperCase()}.`);
  };

  const security = selected ? tokenSecurityFindings(selected, result?.security_findings ?? []) : [];
  const occurrences = selected && result ? result.tokens.filter((token) => token.lexeme === selected.lexeme).length : 0;
  const tokenTypeLabel = selected?.token_type ?? '';

  return <div className="ide-tokens-layout">
    <section className="ide-token-main" aria-label="Token results">
      <div className="ide-token-telemetry" aria-live="polite">
        <div className="ide-token-metrics"><span className="ide-telemetry-strong">{counts.total} tokens</span><span>·</span><span>{counts.valid} valid</span><span>·</span><span>{counts.invalid} invalid</span><span>·</span><span className={`ide-token-analysis-status ${status === 'Stale' ? 'stale' : status === 'Analysis incomplete' ? 'incomplete' : ''}`}>{status}</span></div>
        <div className="ide-token-grammar" title={grammarLabel}>{grammarLabel}</div>
      </div>
      <div className="ide-token-tools">
        <label className="ide-token-search"><span className="material-symbols-outlined" aria-hidden="true">search</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search lexeme, type, category, line:col…" aria-label="Search tokens" /></label>
        <div className="ide-token-filters" role="group" aria-label="Filter tokens">
          <button type="button" className={filter === 'All' ? 'active' : ''} aria-pressed={filter === 'All'} onClick={() => setFilter('All')}>All <span>{counts.total}</span></button>
          <button type="button" className={filter === 'Invalid' ? 'active' : ''} aria-pressed={filter === 'Invalid'} onClick={() => setFilter('Invalid')}>Invalid <span>{counts.invalid}</span></button>
          {categories.map(([category, total]) => <button type="button" key={category} className={filter === category ? 'active' : ''} aria-pressed={filter === category} onClick={() => setFilter(category)}>{category} <span>{total}</span></button>)}
        </div>
        <label className="ide-token-sort">Sort <select aria-label="Sort tokens" value={sort} onChange={(event) => setSort(event.target.value as TokenSort)}><option value="position">Position</option><option value="type">Token type</option></select></label>
        <div className="ide-token-export"><button type="button" title="Copy visible tokens as TSV" onClick={() => void copy()}>Copy TSV</button><button type="button" title="Export visible tokens as CSV" disabled={!result} onClick={() => download('csv')}>CSV</button><button type="button" title="Export visible tokens as JSON" disabled={!result} onClick={() => download('json')}>JSON</button></div>
      </div>
      <div className="ide-token-table" role="table" aria-label="Tokens" aria-rowcount={visible.length + 1} onKeyDown={handleKeyDown}>
        <div className="ide-token-head" role="row"><span role="columnheader">Line:Col</span><span role="columnheader">Lexeme</span><span role="columnheader">Token Type</span><span role="columnheader">Category</span><span role="columnheader">Lexical Status</span><span role="columnheader">Symbol / Semantic Info</span></div>
        <div className="ide-token-scroll" ref={scrollRef} onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)} tabIndex={0} aria-label="Token rows; use arrow keys, Home, End, and Enter">
          {visible.length ? <div className="ide-token-spacer" style={{ height: visible.length * ROW_HEIGHT }}>
            {rows.map((token, offset) => {
              const index = start + offset;
              const isSelected = token.id === selectedTokenId;
              return <div key={token.id} role="row" aria-rowindex={index + 2} aria-selected={isSelected} tabIndex={isSelected || (!selectedTokenId && index === 0) ? 0 : -1} className={`ide-token-row ${isSelected ? 'selected' : ''} ${token.lexical_status}`} style={{ transform: `translateY(${index * ROW_HEIGHT}px)` }} onClick={() => onSelect(token)} onKeyDown={(event) => { if (event.key === 'Enter') onSelect(token); }}>
                <span role="cell" title={positionLabel(token)}>{token.start_line}:{token.start_column}</span><span role="cell" className="ide-token-lexeme" title={visibleLexeme(token.lexeme)}>{visibleLexeme(token.lexeme)}</span><span role="cell" title={token.token_type}>{token.token_type}</span><span role="cell" className="ide-token-category" title={token.category}>{categoryGroup(token.category)}</span><span role="cell" className={`ide-token-status ${token.lexical_status}`}>{token.lexical_status}</span><span role="cell" className="ide-token-info">{token.lexical_status === 'invalid' && onFix ? <button type="button" disabled={!fixEnabled} title={fixEnabled ? 'Propose a rule-first token fix' : 'Rule fix capability is unavailable.'} aria-label={`Fix invalid token ${visibleLexeme(token.lexeme)}`} onClick={event => { event.stopPropagation(); onFix(token); }}>Fix</button> : '—'}</span>
              </div>;
            })}
          </div> : <div className="ide-token-empty">{result ? 'No tokens match this filter.' : 'Run Analyze to inspect tokens from this file.'}</div>}
        </div>
      </div>
    </section>
    {inspectorOpen && <aside className="ide-token-inspector" id="inspectorPanel" aria-label="Token Inspector"><header><strong><span className="material-symbols-outlined" aria-hidden="true">token</span>Token Inspector</strong><button type="button" aria-label="Close token inspector" title="Close inspector" onClick={onToggleInspector}><span className="material-symbols-outlined" aria-hidden="true">close</span></button></header>{selected ? <div className="ide-token-inspector-body">
      <section className="ide-inspector-card"><span className="ide-inspector-label">Selected Lexeme</span><strong className="ide-inspector-lexeme">{visibleLexeme(selected.lexeme)}</strong><span className="ide-inspector-type">{selected.token_type}</span><span className={`ide-token-status ${selected.lexical_status}`}>{selected.lexical_status}</span></section>
      {selected.lexical_status === 'invalid' && onFix && <button type="button" disabled={!fixEnabled} title={fixEnabled ? 'Propose a rule-first token fix' : 'Rule fix capability is unavailable.'} onClick={() => onFix(selected)}>Fix token</button>}
      <dl><dt>Category</dt><dd>{selected.category}</dd><dt>Range</dt><dd>{positionLabel(selected)}</dd><dt>Occurrences in file</dt><dd>{occurrences}</dd></dl>
      <section className="ide-inspector-section"><h3>Beginner explanation</h3><p>{explainToken(tokenTypeLabel, language)}</p></section>
      {security.length > 0 && <section className="ide-inspector-section security"><h3>Security note</h3>{security.map((finding) => <p key={finding.id}>{finding.message}</p>)}</section>}
    </div> : <div className="ide-inspector-empty">Select a token to inspect its details.</div>}</aside>}
    {!inspectorOpen && <button type="button" className="ide-token-inspector-reopen" onClick={onToggleInspector}>Show Inspector</button>}
  </div>;
}
