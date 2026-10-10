import React from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Finding, Severity } from '../api/client';
import { findingCategory } from '../utils/findingCategory';

interface ProblemsPanelProps {
  findings: Finding[];
  selectedFindingId: string | null;
  filter: 'all' | Severity;
  onSelectFilter: (filter: 'all' | Severity) => void;
  onSelectFinding: (findingId: string) => void;
  onNextFinding: () => void;
  onPrevFinding: () => void;
}

export const ProblemsPanel: React.FC<ProblemsPanelProps> = ({
  findings,
  selectedFindingId,
  filter,
  onSelectFilter,
  onSelectFinding,
  onNextFinding,
  onPrevFinding,
}) => {
  const [sortBy, setSortBy] = React.useState<'priority' | 'severity' | 'location' | 'confidence'>('priority');
  const [grouped, setGrouped] = React.useState(false);
  const [collapsed, setCollapsed] = React.useState(false);
  const activeFindings = findings.filter((f) => !f.suppressed);

  const top3Ids = React.useMemo(() => {
    const sortedByPriority = [...activeFindings].sort(
      (a, b) => (b.priority ?? 0) - (a.priority ?? 0) || (b.confidence ?? 0) - (a.confidence ?? 0)
    );
    return new Set(sortedByPriority.slice(0, 3).map((f) => f.id));
  }, [activeFindings]);

  const filteredFindings =
    filter === 'all'
      ? activeFindings
      : activeFindings.filter((f) => f.severity === filter);
  const severityOrder: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
  const sortedFindings = [...filteredFindings].sort((a, b) => {
    if (sortBy === 'priority') {
      const pDiff = (b.priority ?? 0) - (a.priority ?? 0);
      if (Math.abs(pDiff) > 0.0001) return pDiff;
      return (
        severityOrder[a.severity] - severityOrder[b.severity] ||
        a.range.start_line - b.range.start_line
      );
    }
    if (sortBy === 'location') {
      return a.range.start_line - b.range.start_line || a.range.start_col - b.range.start_col;
    }
    if (sortBy === 'confidence') {
      return b.confidence - a.confidence;
    }
    return severityOrder[a.severity] - severityOrder[b.severity];
  });
  const shownFindings = grouped ? [...sortedFindings].sort((a, b) => findingCategory(a).localeCompare(findingCategory(b))) : sortedFindings;

  const getSeverityIcon = (sev: Severity) => {
    switch (sev) {
      case 'critical':
        return <AlertOctagon size={14} color="var(--critical)" />;
      case 'high':
        return <ShieldAlert size={14} color="var(--high)" />;
      case 'medium':
        return <AlertTriangle size={14} color="var(--medium)" />;
      case 'low':
        return <Info size={14} color="var(--low)" />;
      case 'info':
      default:
        return <CheckCircle2 size={14} color="var(--info)" />;
    }
  };

  const getSeverityColor = (sev: Severity) => {
    switch (sev) {
      case 'critical':
        return 'var(--critical)';
      case 'high':
        return 'var(--high)';
      case 'medium':
        return 'var(--medium)';
      case 'low':
        return 'var(--low)';
      case 'info':
      default:
        return 'var(--info)';
    }
  };

  return (
    <div style={containerStyle}>
      {/* Problems Toolbar */}
      <div style={toolbarStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button style={titleStyle} onClick={() => setCollapsed((value) => !value)} aria-expanded={!collapsed}>PROBLEMS {activeFindings.length}</button>
        </div>

        {/* Severity Filter Pills */}
        <div style={filterGroupStyle}>
          {(['all', 'critical', 'high', 'medium', 'low'] as const).map((sev) => {
            const isActive = filter === sev;
            const count =
              sev === 'all'
                ? activeFindings.length
                : activeFindings.filter((f) => f.severity === sev).length;

            return (
              <button
                key={sev}
                style={{
                  ...filterBtnStyle,
                  backgroundColor: isActive ? 'var(--panel-3)' : 'transparent',
                  borderColor: isActive ? 'var(--accent)' : 'transparent',
                  color: isActive ? 'var(--text)' : 'var(--muted)',
                }}
                onClick={() => onSelectFilter(sev)}
                aria-label={`Filter by ${sev}`}
              >
                  {sev === 'all' ? 'All' : sev[0].toUpperCase() + sev.slice(1)} {count}
              </button>
            );
          })}
        </div>
        <select aria-label="Sort problems" value={sortBy} onChange={(event) => setSortBy(event.target.value as typeof sortBy)} style={{ background: 'var(--panel)', color: 'var(--text-secondary)', border: '1px solid var(--border)', fontSize: 10 }}>
          <option value="priority">Priority</option><option value="severity">Severity</option><option value="location">Location</option><option value="confidence">Confidence</option>
        </select>
        <label style={{ fontSize: 10, color: 'var(--muted)', whiteSpace: 'nowrap' }}><input type="checkbox" checked={grouped} onChange={(event) => setGrouped(event.target.checked)} /> Group</label>

        {/* Next / Previous Shortcuts */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            style={navBtnStyle}
            onClick={onPrevFinding}
            title="Previous Problem (Shift+F8)"
            aria-label="Previous Problem"
          >
            <ChevronUp size={14} />
          </button>
          <button
            style={navBtnStyle}
            onClick={onNextFinding}
            title="Next Problem (F8)"
            aria-label="Next Problem"
          >
            <ChevronDown size={14} />
          </button>
        </div>
      </div>

      {/* Problems Table / List */}
      {!collapsed && <div style={tableContainerStyle}>
        {filteredFindings.length === 0 ? (
          <div style={emptyStyle}>
            {activeFindings.length === 0
              ? <span style={{ color: 'var(--success)' }}>No security issues found</span>
              : `No ${filter} severity issues found.`}
          </div>
        ) : (
          <table style={tableStyle}>
            <thead>
              <tr style={thRowStyle}>
                <th style={{ ...thStyle, width: '110px' }}>Severity</th>
                <th style={{ ...thStyle, width: '130px' }}>CWE</th>
                <th style={thStyle}>Message</th>
                <th style={{ ...thStyle, width: '100px', textAlign: 'right' }}>Location</th>
              </tr>
            </thead>
            <tbody>
              {shownFindings.map((finding) => {
                const isSelected = finding.id === selectedFindingId;
                const sevColor = getSeverityColor(finding.severity);

                return (
                  <tr
                    key={finding.id}
                    style={{
                      ...trStyle,
                      backgroundColor: 'transparent',
                      borderLeft: isSelected ? `3px solid ${sevColor}` : '3px solid transparent',
                    }}
                    onClick={() => onSelectFinding(finding.id)}
                    onKeyDown={(event) => { if (event.key === 'Enter') onSelectFinding(finding.id); }}
                    tabIndex={0}
                  >
                    <td style={tdStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {getSeverityIcon(finding.severity)}
                        <span
                          style={{
                            color: sevColor,
                            fontWeight: 600,
                            fontSize: '11px',
                            textTransform: 'uppercase',
                          }}
                        >
                          {finding.severity}
                        </span>
                      </div>
                    </td>
                    <td style={tdStyle}>
                      <code style={ruleCodeStyle}>{finding.cwe || finding.rule_id}</code>
                    </td>
                    <td style={tdStyle}>
                      <span style={messageStyle}>{grouped ? `${findingCategory(finding)} · ${finding.title}` : finding.title || finding.message}</span>
                      {top3Ids.has(finding.id) && (
                        <span
                          data-qa="fix-first-badge"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '1px 6px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 700,
                            backgroundColor: 'var(--bg-warning)',
                            color: 'var(--text-warning)',
                            border: '1px solid var(--text-warning)',
                            marginLeft: '8px',
                            letterSpacing: '0.2px',
                          }}
                          title="Priority ranking: recommended to fix first"
                        >
                          Fix first
                        </span>
                      )}
                    </td>
                    <td style={{ ...tdStyle, textAlign: 'right' }}>
                      <span style={locStyle}>
                        Ln {finding.range.start_line}:{finding.range.start_col}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>}
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  height: '100%',
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: 'var(--panel)',
  overflow: 'hidden',
};

const toolbarStyle: React.CSSProperties = {
  height: '32px',
  minHeight: '32px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 12px',
  backgroundColor: 'var(--panel-2)',
  borderBottom: '1px solid var(--border)',
};

const titleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
  background: 'transparent', border: 0, cursor: 'pointer',
};

const filterGroupStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '2px',
};

const filterBtnStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 600,
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid transparent',
  cursor: 'pointer',
};

const navBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '3px',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--muted)',
};

const tableContainerStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
};

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  textAlign: 'left',
  fontSize: '12px',
};

const thRowStyle: React.CSSProperties = {
  backgroundColor: 'var(--panel)',
  borderBottom: '1px solid var(--border)',
  position: 'sticky',
  top: 0,
  zIndex: 2,
};

const thStyle: React.CSSProperties = {
  padding: '6px 12px',
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.3px',
};

const trStyle: React.CSSProperties = {
  borderBottom: '1px solid var(--border-subtle)',
  cursor: 'pointer',
  transition: 'background-color var(--transition-fast)',
};

const tdStyle: React.CSSProperties = {
  padding: '6px 12px',
  whiteSpace: 'nowrap',
};

const ruleCodeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--accent)',
};

const messageStyle: React.CSSProperties = {
  color: 'var(--text)',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: '500px',
  display: 'inline-block',
  verticalAlign: 'middle',
};

const locStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--muted)',
};

const emptyStyle: React.CSSProperties = {
  padding: '24px',
  color: 'var(--muted)',
  fontSize: '12px',
  textAlign: 'center',
  fontStyle: 'italic',
};
