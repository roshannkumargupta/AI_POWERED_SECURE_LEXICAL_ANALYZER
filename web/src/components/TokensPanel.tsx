import React, { useMemo, useRef, useState } from 'react';
import type { AnalysisResult, MLInsightsResponse } from '../api/client';
import { adaptTokens, visibleText } from '../model/adapt';

type Props = {
  result: AnalysisResult | null;
  language: string;
  selectedIndex: number | null;
  selectedFindingId: string | null;
  mlMode: string;
  ml: MLInsightsResponse | null;
  loadingML: boolean;
  onSelectToken: (index: number) => void;
  onSelectFinding: (id: string) => void;
  onLoadML: (index: number) => void;
  onTokenMap: (mode: 'off' | 'security' | 'full') => void;
  tokenMap: 'off' | 'security' | 'full';
  category: string;
  onCategoryChange: (category: string) => void;
  showAll?: boolean;
  mainFilter?: 'All' | 'Security' | 'Lexical' | 'Syntax';
  groups?: string[];
};

const rowHeight = 32;

export const TokensPanel: React.FC<Props> = ({
  result,
  selectedIndex,
  selectedFindingId,
  onSelectToken,
  onSelectFinding,
  showAll = false,
  mainFilter = 'All',
  groups = [],
}) => {
  const rows = useMemo(() => adaptTokens(result), [result]);
  const [offset, setOffset] = useState(0);
  const scroller = useRef<HTMLDivElement>(null);
  const rowCount = rows.filter(
    (row) => row.security === 'insecure' || row.lexical === 'error'
  ).length;
  const filtered = rows.filter((row) => {
    if (!showAll && row.security !== 'insecure' && row.lexical !== 'error') return false;
    if (mainFilter === 'Security' && row.security !== 'insecure') return false;
    if (mainFilter === 'Lexical' && row.lexical !== 'error') return false;
    if (mainFilter === 'Syntax' && row.group !== 'syntax') return false;
    return groups.length === 0 || groups.includes(row.group);
  });
  const visibleCount = 200;
  const start =
    rows.length > visibleCount ? Math.min(offset, Math.max(0, filtered.length - visibleCount)) : 0;
  const visible = filtered.slice(start, start + visibleCount);
  const selected =
    rows.find((row) => row.rawTokenIds.some((id) => Number(id.slice(6)) === selectedIndex)) ||
    rows.find((row) => row.findingIds.includes(selectedFindingId || ''));
  const jump = (row: (typeof rows)[number]) => {
    const index = Number(row.rawTokenIds[0]?.slice(6));
    if (Number.isFinite(index)) onSelectToken(index);
    if (row.primaryFindingId) onSelectFinding(row.primaryFindingId);
  };
  const key = (event: React.KeyboardEvent<HTMLTableElement>) => {
    if (!['ArrowDown', 'ArrowUp', 'Enter', 'Escape'].includes(event.key)) return;
    if (event.key === 'Escape') {
      (document.querySelector('.monaco-editor textarea') as HTMLElement | null)?.focus();
      return;
    }
    event.preventDefault();
    const current = filtered.findIndex((row) =>
      row.rawTokenIds.some((id) => Number(id.slice(6)) === selectedIndex)
    );
    if (event.key === 'Enter') {
      if (filtered[current]) jump(filtered[current]);
      return;
    }
    const next =
      filtered[
        Math.max(0, Math.min(filtered.length - 1, current + (event.key === 'ArrowDown' ? 1 : -1)))
      ];
    if (next) jump(next);
  };

  return (
    <div className="ui6-token-view">
      {!result ? (
        <div className="ui5-empty">Open or paste code to analyse it.</div>
      ) : (
        <>
          <div className="ui6-table-controls" aria-label="Token table">
            {showAll && <span>Showing all tokens</span>}
            <span className="ui6-problems">{rowCount} problem rows</span>
          </div>
          {!rows.length && result === null ? (
            <div className="ui5-empty">Open or paste code to analyse it.</div>
          ) : !rowCount && !showAll ? (
            <div className="ui5-empty">
              No security or lexical problems found{' '}
              <span>
                ({result?.summary.critical ?? 0} critical, {result?.summary.high ?? 0} high,{' '}
                {result?.summary.lexical_errors ?? 0} lexical)
              </span>
            </div>
          ) : !filtered.length ? (
            <div className="ui5-empty">No rows match the filters.</div>
          ) : (
            <div
              className="ui6-table-scroll"
              ref={scroller}
              onScroll={(event) => setOffset(Math.floor(event.currentTarget.scrollTop / rowHeight))}
            >
              <table
                data-qa="table"
                className="ui6-token-table"
                onKeyDown={key}
                aria-label="Tokens"
              >
                <colgroup>
                  <col style={{ width: '13%' }} />
                  <col style={{ width: '31%' }} />
                  <col style={{ width: '17%' }} />
                  <col style={{ width: '18%' }} />
                  <col style={{ width: '21%' }} />
                </colgroup>
                <thead>
                  <tr>
                    <th>Ln:Col</th>
                    <th>Lexeme</th>
                    <th>Type</th>
                    <th>Lexical</th>
                    <th>Security</th>
                  </tr>
                </thead>
                <tbody>
                  {start > 0 && (
                    <tr aria-hidden="true" className="ui6-spacer">
                      <td colSpan={5} style={{ height: start * rowHeight }} />{' '}
                    </tr>
                  )}
                  {visible.map((row) => {
                    const selectedRow =
                      row.rawTokenIds.some((id) => Number(id.slice(6)) === selectedIndex) ||
                      row.findingIds.includes(selectedFindingId || '');
                    return (
                      <tr
                        key={row.id}
                        tabIndex={0}
                        aria-selected={selectedRow}
                        onClick={() => jump(row)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') jump(row);
                        }}
                      >
                        <td>
                          {row.line}:{row.col}
                        </td>
                        <td className="ui6-lexeme" title={row.lexeme}>
                          {visibleText(row.lexeme)}
                        </td>
                        <td>{row.type}</td>
                        <td>
                          <span className={`ui6-badge ${row.lexical}`}>{row.lexical}</span>
                        </td>
                        <td>
                          <span className={`ui6-badge ${row.security}`}>
                            {row.security === 'na' ? 'n/a' : row.security}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                  {start + visible.length < filtered.length && (
                    <tr aria-hidden="true" className="ui6-spacer">
                      <td
                        colSpan={5}
                        style={{ height: (filtered.length - start - visible.length) * rowHeight }}
                      />
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
          {selected && (
            <details className="ui6-lexical-details">
              <summary>Lexical details</summary>
              <div>
                Raw token parts:{' '}
                {selected.rawTokenIds.map((id) => {
                  const rawIndex = Number(id.slice(6));
                  const token = result?.tokens[rawIndex];
                  return token ? (
                    <span key={id}>
                      {' '}
                      {token.token_type}:{' '}
                      <code>{visibleText(token.token ?? token.text ?? '')}</code> (
                      {token.range?.start_line ?? token.line}:{token.range?.start_col ?? token.col})
                    </span>
                  ) : null;
                })}
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
};
