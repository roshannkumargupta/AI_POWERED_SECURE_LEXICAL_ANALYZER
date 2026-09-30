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
  const activeFindings = findings.filter((f) => !f.suppressed);

  const filteredFindings =
    filter === 'all'
      ? activeFindings
      : activeFindings.filter((f) => f.severity === filter);

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
          <span style={titleStyle}>Problems</span>
          <span style={badgeCountStyle}>{activeFindings.length}</span>
        </div>

        {/* Severity Filter Pills */}
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
                {sev.toUpperCase()} ({count})
              </button>
            );
          })}
        </div>

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
      <div style={tableContainerStyle}>
        {filteredFindings.length === 0 ? (
          <div style={emptyStyle}>
            {activeFindings.length === 0
              ? 'No issues detected in current code.'
              : `No ${filter} severity issues found.`}
          </div>
        ) : (
          <table style={tableStyle}>
            <thead>
              <tr style={thRowStyle}>
                <th style={{ ...thStyle, width: '110px' }}>Severity</th>
                <th style={{ ...thStyle, width: '130px' }}>Rule ID</th>
                <th style={thStyle}>Message</th>
                <th style={{ ...thStyle, width: '100px', textAlign: 'right' }}>Location</th>
              </tr>
            </thead>
            <tbody>
              {filteredFindings.map((finding) => {
                const isSelected = finding.id === selectedFindingId;
                const sevColor = getSeverityColor(finding.severity);

                return (
                  <tr
                    key={finding.id}
                    style={{
                      ...trStyle,
                      backgroundColor: isSelected ? 'var(--panel-3)' : 'transparent',
                      borderLeft: isSelected ? `3px solid ${sevColor}` : '3px solid transparent',
                    }}
                    onClick={() => onSelectFinding(finding.id)}
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
                      <code style={ruleCodeStyle}>{finding.rule_id}</code>
                    </td>
                    <td style={tdStyle}>
                      <span style={messageStyle}>{finding.message}</span>
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
      </div>
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
};

const badgeCountStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 600,
  padding: '1px 5px',
  borderRadius: 'var(--radius-full)',
  backgroundColor: 'var(--panel-3)',
  color: 'var(--text)',
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
