import React from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { Finding, Severity } from '../api/client';
import { ProblemRow } from './ProblemRow';
import {
  filterFindings,
  sortFindings,
  getTopPriorityFindingIds,
  ProblemsSortBy,
} from '../model/problemsSelection';

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
  const [sortBy, setSortBy] = React.useState<ProblemsSortBy>('priority');
  const [grouped, setGrouped] = React.useState(false);
  const [collapsed, setCollapsed] = React.useState(false);

  const activeFindings = React.useMemo(() => findings.filter((f) => !f.suppressed), [findings]);
  const top3Ids = React.useMemo(
    () => getTopPriorityFindingIds(activeFindings, 3),
    [activeFindings]
  );
  const filteredFindings = React.useMemo(
    () => filterFindings(findings, filter),
    [findings, filter]
  );
  const shownFindings = React.useMemo(
    () => sortFindings(filteredFindings, sortBy, grouped),
    [filteredFindings, sortBy, grouped]
  );

  return (
    <div style={containerStyle}>
      <div style={toolbarStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            style={titleStyle}
            onClick={() => setCollapsed(!collapsed)}
            aria-label="Toggle problems list"
          >
            Problems ({activeFindings.length})
          </button>
        </div>

        <div style={filterGroupStyle}>
          {(['all', 'critical', 'high', 'medium', 'low', 'info'] as const).map((sev) => {
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

        <select
          aria-label="Sort problems"
          value={sortBy}
          onChange={(event) => setSortBy(event.target.value as ProblemsSortBy)}
          style={{
            background: 'var(--panel)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border)',
            fontSize: 10,
          }}
        >
          <option value="priority">Priority</option>
          <option value="severity">Severity</option>
          <option value="location">Location</option>
          <option value="confidence">Confidence</option>
        </select>

        <label style={{ fontSize: 10, color: 'var(--muted)', whiteSpace: 'nowrap' }}>
          <input
            type="checkbox"
            checked={grouped}
            onChange={(event) => setGrouped(event.target.checked)}
          />{' '}
          Group
        </label>

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

      {!collapsed && (
        <div style={tableContainerStyle}>
          {filteredFindings.length === 0 ? (
            <div style={emptyStyle}>
              {activeFindings.length === 0 ? (
                <span style={{ color: 'var(--success)' }}>No security issues found</span>
              ) : (
                `No ${filter} severity issues found.`
              )}
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
                {shownFindings.map((finding) => (
                  <ProblemRow
                    key={finding.id}
                    finding={finding}
                    isSelected={finding.id === selectedFindingId}
                    isTopPriority={top3Ids.has(finding.id)}
                    grouped={grouped}
                    onSelect={onSelectFinding}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
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
  background: 'transparent',
  border: 0,
  cursor: 'pointer',
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

const emptyStyle: React.CSSProperties = {
  padding: '24px',
  color: 'var(--muted)',
  fontSize: '12px',
  textAlign: 'center',
  fontStyle: 'italic',
};
