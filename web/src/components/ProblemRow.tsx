import React from 'react';
import { AlertOctagon, ShieldAlert, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { Finding, Severity } from '../api/client';
import { findingCategory } from '../utils/findingCategory';

interface ProblemRowProps {
  finding: Finding;
  isSelected: boolean;
  isTopPriority: boolean;
  grouped: boolean;
  onSelect: (id: string) => void;
}

export const ProblemRow: React.FC<ProblemRowProps> = ({
  finding,
  isSelected,
  isTopPriority,
  grouped,
  onSelect,
}) => {
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

  const sevColor = getSeverityColor(finding.severity);

  return (
    <tr
      style={{
        cursor: 'pointer',
        transition: 'background-color 150ms ease',
        backgroundColor: 'transparent',
        borderLeft: isSelected ? `3px solid ${sevColor}` : '3px solid transparent',
      }}
      onClick={() => onSelect(finding.id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') onSelect(finding.id);
      }}
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
        <span style={messageStyle}>
          {grouped
            ? `${findingCategory(finding)} · ${finding.title}`
            : finding.title || finding.message}
        </span>
        {isTopPriority && (
          <span
            data-qa="fix-first-badge"
            style={{
              marginLeft: '6px',
              fontSize: '9px',
              color: 'var(--amber)',
              background: 'var(--panel-2)',
              borderRadius: '2px',
              padding: '1px 4px',
              border: '1px solid var(--border)',
            }}
          >
            Fix first
          </span>
        )}
      </td>
      <td
        style={{
          ...tdStyle,
          textAlign: 'right',
          color: 'var(--muted)',
          fontFamily: 'var(--font-code)',
        }}
      >
        Ln {finding.range.start_line}, Col {finding.range.start_col}
      </td>
    </tr>
  );
};

const tdStyle: React.CSSProperties = {
  padding: '6px 12px',
  borderBottom: '1px solid var(--border)',
  verticalAlign: 'middle',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

const ruleCodeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--accent)',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 4px',
  borderRadius: '3px',
};

const messageStyle: React.CSSProperties = {
  fontWeight: 400,
  color: 'var(--text)',
};
