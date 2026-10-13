import { useEffect, useMemo, useState } from 'react';
import { apiClient, type AnalysisResultV2, type MLInsightsResponse, type TokenV2 } from '../../api/client';
import type { Range } from '../../utils/offsets';

export type IDEFinding = AnalysisResultV2['security_findings'][number];
interface Props { result: AnalysisResultV2 | null; source: string; language: string; tokens: TokenV2[]; selectedFindingId: string | null; dataFlowPathId: string | null; onSelect(finding: IDEFinding | null): void; onToggleFlow(pathId: string | null): void; onJump(range: Range): void; onFeedback(finding: IDEFinding): void; onExplain?(finding: IDEFinding): void; onFix?(finding: IDEFinding): void; fixEnabled?: boolean }

function overlaps(a: Range, b: Range) { return (a.start_line < b.end_line || a.start_line === b.end_line && a.start_col < b.end_col) && (a.end_line > b.start_line || a.end_line === b.start_line && a.end_col > b.start_col); }

export function SecurityPanel({ result, source, language, tokens, selectedFindingId, dataFlowPathId, onSelect, onToggleFlow, onJump, onFeedback, onExplain, onFix, fixEnabled = false }: Props) {
  const findings = result?.security_findings ?? [];
  const selected = findings.find(finding => finding.id === selectedFindingId) ?? null;
  const path = selected?.taint_path_id ? result?.taint_paths.find(item => item.id === selected.taint_path_id) ?? null : null;
  const tokenIndex = useMemo(() => selected ? tokens.findIndex(token => overlaps(selected.range, { start_line: token.start_line, start_col: token.start_column, end_line: token.end_line, end_col: token.end_column })) : -1, [selected, tokens]);
  const [insights, setInsights] = useState<MLInsightsResponse | null>(null);
  const [insightStatus, setInsightStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  useEffect(() => {
    if (!selected || tokenIndex < 0) { setInsights(null); setInsightStatus('idle'); return; }
    const controller = new AbortController();
    setInsightStatus('loading');
    apiClient.getMLInsights({ source, language, token_index: tokenIndex }).then(value => { if (!controller.signal.aborted) { setInsights(value); setInsightStatus('idle'); } }).catch(() => { if (!controller.signal.aborted) { setInsights(null); setInsightStatus('error'); } });
    return () => controller.abort();
  }, [selected, tokenIndex, source, language]);
  const toolStatus = result?.tools ?? [];
  return <div className="ide-security-layout">
    <section className="ide-security-list" aria-label="Security findings"><header className="ide-p4-toolbar"><strong>Security Findings</strong><span>{findings.length}</span></header>{findings.length ? findings.map(finding => <div key={finding.id} className="ide-security-row-wrap"><button type="button" className={`ide-security-row ${finding.id === selectedFindingId ? 'selected' : ''}`} onClick={() => onSelect(finding)}><span className={`ide-severity ${finding.severity}`}>security</span><span><strong>{finding.title}</strong><small>{(finding.cwe ?? []).join(', ') || 'CWE unavailable'} · {finding.severity} · {finding.certainty}</small></span><code>{finding.range.start_line}:{finding.range.start_col}</code></button>{onExplain && <button type="button" className="ide-feedback-button" onClick={() => onExplain(finding)}>Explain</button>}{onFix && <button type="button" className="ide-fix-inline" disabled={!fixEnabled} title={fixEnabled ? 'Propose a fix for this finding' : 'Fix capability is unavailable.'} onClick={() => onFix(finding)}>Fix</button>}</div>) : <p className="ide-p4-empty">{result?.omissions.length || toolStatus.some(tool => tool.status === 'unavailable') ? 'Analysis incomplete; security checks did not all run.' : result ? 'No findings detected by checks run' : 'Run Analyze to see security findings.'}</p>}</section>
    <aside className="ide-finding-detail" aria-label="Security finding details">{selected ? <>
      <header><div><span className={`ide-severity ${selected.severity}`}>security</span><h3>{selected.title}</h3><p>{(selected.cwe ?? []).join(', ') || 'CWE unavailable'} · {selected.rule_id}</p></div><button type="button" aria-label="Clear selected finding" title="Clear selection" onClick={() => onSelect(null)}>×</button></header>
      <div className="ide-finding-content"><dl><dt>Severity</dt><dd>{selected.severity}</dd><dt>Certainty</dt><dd>{selected.certainty}</dd><dt>Range</dt><dd><button type="button" onClick={() => onJump(selected.range)}>{selected.range.start_line}:{selected.range.start_col}–{selected.range.end_line}:{selected.range.end_col}</button></dd><dt>Tools</dt><dd>{selected.tool_provenance?.join(', ') || 'Tool provenance unavailable'}</dd></dl>
        <section><h4>Finding</h4><p>{selected.message}</p></section><section><h4>Evidence</h4><pre>{JSON.stringify(selected.evidence, null, 2)}</pre></section><section><h4>Remediation</h4><p>{selected.remediation || 'No remediation was provided by the finding.'}</p></section><section><h4>Rule</h4><p>{selected.rule_id}</p></section>
        {path && <section className="ide-taint-flow"><header><h4>Data Flow</h4><button type="button" aria-pressed={dataFlowPathId === path.id} onClick={() => onToggleFlow(dataFlowPathId === path.id ? null : path.id)}>{dataFlowPathId === path.id ? 'Hide Data Flow' : 'Show Data Flow'}</button></header><ol>{path.steps.map((step, index) => <li key={`${path.id}-${index}`}><button type="button" onClick={() => onJump(step.range)}><b>{index + 1}</b><span className={`role ${step.role}`}>{step.role}</span><code>{step.text}</code><small>Ln {step.range.start_line}, Col {step.range.start_col}</small>{step.note && <p>{step.note}</p>}</button></li>)}</ol>{!path.complete && <p className="ide-p4-notice warning">Path incomplete{path.limitation ? `: ${path.limitation}` : '.'}</p>}</section>}
        <section><h4>ML Probability and Occlusion</h4>{insightStatus === 'loading' ? <p>Loading ML insights…</p> : insightStatus === 'error' ? <p>ML insights unavailable.</p> : insights?.error ? <p>ML insights unavailable: {insights.error}</p> : insights?.probabilities ? <><p>Prediction: {insights.predicted_label || 'Label unavailable'}</p>{Object.entries(insights.probabilities).map(([label, value]) => <p key={label}>{label}: {(value * 100).toFixed(1)}%</p>)}{Object.entries(insights.feature_group_drops ?? {}).length > 0 && <div><h5>Feature-group occlusion impact</h5>{Object.entries(insights.feature_group_drops ?? {}).sort(([, a], [, b]) => b - a).map(([name, value]) => <p key={name}>{name}: {value.toFixed(3)}</p>)}</div>}</> : <p>{tokenIndex < 0 ? 'No overlapping analyzed token is available for ML insights.' : 'ML insights unavailable for this token.'}</p>}</section>
        <button type="button" className="ide-feedback-button" onClick={() => onFeedback(selected)}>Flag as false positive</button>{onExplain && <button type="button" className="ide-feedback-button" onClick={() => onExplain(selected)}>Explain finding with AI</button>}
      </div>
    </> : <p className="ide-p4-empty">Select a finding to inspect evidence, remediation, model output, and data flow.</p>}</aside>
  </div>;
}
