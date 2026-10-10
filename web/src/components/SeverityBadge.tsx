import React from 'react';
import { AlertOctagon, ShieldAlert, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { Severity } from '../api/client';
import { sevBadgeStyle } from './findingStyles';

export interface SeverityBadgeProps {
  severity: Severity;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  switch (severity) {
    case 'critical':
      return (
        <span
          style={{
            ...sevBadgeStyle,
            color: 'var(--critical)',
            backgroundColor: 'var(--critical-subtle)',
          }}
        >
          <AlertOctagon size={13} />
          CRITICAL
        </span>
      );
    case 'high':
      return (
        <span
          style={{
            ...sevBadgeStyle,
            color: 'var(--high)',
            backgroundColor: 'var(--high-subtle)',
          }}
        >
          <ShieldAlert size={13} />
          HIGH
        </span>
      );
    case 'medium':
      return (
        <span
          style={{
            ...sevBadgeStyle,
            color: 'var(--medium)',
            backgroundColor: 'var(--medium-subtle)',
          }}
        >
          <AlertTriangle size={13} />
          MEDIUM
        </span>
      );
    case 'low':
      return (
        <span
          style={{ ...sevBadgeStyle, color: 'var(--low)', backgroundColor: 'var(--low-subtle)' }}
        >
          <Info size={13} />
          LOW
        </span>
      );
    case 'info':
    default:
      return (
        <span
          style={{
            ...sevBadgeStyle,
            color: 'var(--info)',
            backgroundColor: 'var(--info-subtle)',
          }}
        >
          <CheckCircle2 size={13} />
          INFO
        </span>
      );
  }
};
