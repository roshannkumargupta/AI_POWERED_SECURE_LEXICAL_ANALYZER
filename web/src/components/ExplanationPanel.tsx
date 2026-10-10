import React, { useEffect, useMemo, useState } from 'react';
import type { AnalysisResult, Finding, Fix } from '../api/client';
import {
  adaptTokens,
  confidenceText,
  explanationText,
  findingGroup,
  foundBy,
} from '../model/adapt';
import { extractEditText } from '../utils/diff';
import { ExplanationActionBar } from './ExplanationActionBar';

type Props = {
  analysis: AnalysisResult | null;
  source: string;
  selectedIndex: number | null;
  selectedFinding: Finding | null;
  onApplyFix: (fix: Fix, finding: Finding) => void;
  onFalsePositive: (finding: Finding) => void;
  isStale?: boolean;
};

const titleCase = (value: string) => (value ? value[0].toUpperCase() + value.slice(1) : value);

export const ExplanationPanel: React.FC<Props> = ({
  analysis,
  source,
  selectedIndex,
  selectedFinding,
  onApplyFix,
  onFalsePositive,
  isStale = false,
}) => {
  const rows = useMemo(() => adaptTokens(analysis), [analysis]);
  const [findingIndex, setFindingIndex] = useState(0);
  const [fixIndex, setFixIndex] = useState(0);
  const [copiedAdvice, setCopiedAdvice] = useState(false);

  const row = rows.find((item) =>
    item.rawTokenIds.some((id) => Number(id.slice(6)) === selectedIndex)
  );

  const related = row
    ? row.findingIds
        .map((id) => analysis?.findings.find((finding) => finding.id === id))
        .filter((item): item is Finding => Boolean(item))
    : selectedFinding
      ? [selectedFinding]
      : [];

  const relatedIds = related.map((item) => item.id).join('|');

  useEffect(() => {
    setFindingIndex(0);
    setFixIndex(0);
    setCopiedAdvice(false);
  }, [selectedIndex, relatedIds]);

  const finding = related[findingIndex] || selectedFinding;
  const fixes = finding?.fixes || [];
  const fix = fixes[fixIndex];

  const badge = !finding
    ? row?.lexical === 'error'
      ? ['Lexical error', 'error']
      : row?.security === 'insecure'
        ? ['Valid but insecure', 'insecure']
        : ['Valid and safe', 'safe']
    : finding.kind === 'lexical'
      ? ['Lexical error', 'error']
      : finding.kind === 'syntax'
        ? ['Syntax error', 'error']
        : ['Valid but insecure', 'insecure'];

  const findingType =
    finding?.kind === 'lexical' || finding?.kind === 'syntax' ? finding.rule_id : finding?.cwe;
  const group = finding ? titleCase(findingGroup(finding)) : '';

  const oldText = extractEditText(source, fix?.edits);

  const adviceText =
    finding?.explanation ||
    (row ? explanationText(row, undefined) : '') ||
    finding?.message ||
    'Review the security implications of this construct and apply defense-in-depth sanitization or parameterized alternatives.';

  const handleCopyAdvice = () => {
    const toCopy = `${finding?.title || finding?.rule_id || 'Security Advice'}:\n${adviceText}`;
    void navigator.clipboard.writeText(toCopy);
    setCopiedAdvice(true);
    setTimeout(() => setCopiedAdvice(false), 2000);
  };

  const hasEdit = Boolean(fix?.edits && fix.edits.length > 0 && fix.confidence !== 'manual');
  const isVerifiedSafe = fix?.confidence === 'safe' && Boolean(fix.verification?.verified);

  if (!row && !finding) {
    return (
      <section className="ui6-explanation" aria-label="Explanation">
        <span className="ui5-empty">Select a token or problem to see why it was flagged.</span>
      </section>
    );
  }

  return (
    <section
      data-qa="explain"
      className="ui6-explanation"
      aria-label="Explanation"
      style={{
        display: 'flex',
        flexDirection: 'column',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <header className="ui6-explain-header" style={{ flexShrink: 0 }}>
        <code>{row?.lexeme || finding?.title}</code>
        <span className={`ui6-badge ${badge[1]}`}>{badge[0]}</span>
        {findingType && <span className="ui6-meta-pill">{findingType}</span>}
        {finding && (
          <>
            <span className="ui6-meta-pill">{titleCase(finding.severity)}</span>
            <span className="ui6-meta-pill">{group}</span>
            {finding.attack?.map((attack) => (
              <span className="ui6-meta-pill" key={attack}>
                ATT&amp;CK {attack}
              </span>
            ))}
          </>
        )}
        {related.length > 1 && (
          <button
            className="ui6-switch"
            onClick={() => setFindingIndex((findingIndex + 1) % related.length)}
          >
            {findingIndex + 1} of {related.length}
          </button>
        )}
      </header>

      {/* Scrollable Body: Finding details & Diff/Advice */}
      <div
        className="ui6-explain-body"
        style={{
          flex: 1,
          minHeight: 0,
          overflowY: 'auto',
          marginTop: '6px',
        }}
      >
        <div>
          <p>{adviceText}</p>
          {finding && (
            <div className="ui6-found">
              Type: <strong>{finding.title || finding.rule_id}</strong> — Found by:{' '}
              <strong>{foundBy(finding) || 'rule-based analysis'}</strong>
            </div>
          )}
        </div>

        {/* Fix Column (Always present for flagged items) */}
        <div className="ui6-fix-column">
          <div className="ui6-fix-heading">
            <span>Suggested fix (rule-based)</span>
            {hasEdit ? (
              <span
                className={`ui6-badge ${isVerifiedSafe ? 'safe' : 'insecure'}`}
                style={{ marginLeft: 6 }}
              >
                {isVerifiedSafe ? 'verified' : 'review'}
              </span>
            ) : (
              <span className="ui6-badge na" style={{ marginLeft: 6 }}>
                advice
              </span>
            )}
            {fixes.length > 1 && (
              <button
                className="ui6-switch"
                onClick={() => setFixIndex((fixIndex + 1) % fixes.length)}
              >
                Fix {fixIndex + 1} of {fixes.length}
              </button>
            )}
          </div>

          {hasEdit && fix ? (
            <>
              <pre
                style={{
                  maxHeight: '120px',
                  overflowY: 'auto',
                  margin: '4px 0',
                }}
              >
                <span>- {oldText || finding?.message}</span>
                {'\n'}
                <span>+{fix.edits.map((e) => e.new_text).join('')}</span>
              </pre>
              <div className="ui6-confidence">{confidenceText(finding)}</div>
            </>
          ) : (
            <div style={{ marginTop: '6px', color: 'var(--text-secondary)' }}>
              <p style={{ margin: '0 0 4px', fontStyle: 'italic' }}>
                No automatic fix for this rule.
              </p>
              <div
                style={{
                  background: 'var(--surface-2)',
                  padding: '6px 8px',
                  borderRadius: 4,
                  border: '1px solid var(--border)',
                  fontSize: 10,
                  lineHeight: 1.4,
                }}
              >
                {finding?.explanation ||
                  'Architectural remediation required: manual code inspection and design modifications are necessary for this vulnerability.'}
              </div>
            </div>
          )}
        </div>
      </div>

      <ExplanationActionBar
        hasEdit={hasEdit}
        fix={fix}
        finding={finding || undefined}
        isStale={isStale}
        isVerifiedSafe={isVerifiedSafe}
        copiedAdvice={copiedAdvice}
        onApplyFix={onApplyFix}
        onCopyAdvice={handleCopyAdvice}
        onFalsePositive={onFalsePositive}
      />
    </section>
  );
};
