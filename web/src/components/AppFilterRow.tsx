import React from 'react';
import { Finding } from '../api/client';

interface AppFilterRowProps {
  onOpenProblems: () => void;
  analysisExists: boolean;
  activeFindings: Finding[];
  isStale: boolean;
  tokenMainFilter: 'All' | 'Security' | 'Lexical' | 'Syntax';
  onSelectTokenMainFilter: (filter: 'All' | 'Security' | 'Lexical' | 'Syntax') => void;
  tokenGroups: string[];
  onToggleTokenGroup: (group: 'dangerous' | 'suspicious' | 'malicious') => void;
  showAllTokens: boolean;
  onToggleShowAllTokens: (show: boolean) => void;
}

export const AppFilterRow: React.FC<AppFilterRowProps> = ({
  onOpenProblems,
  analysisExists,
  activeFindings,
  isStale,
  tokenMainFilter,
  onSelectTokenMainFilter,
  tokenGroups,
  onToggleTokenGroup,
  showAllTokens,
  onToggleShowAllTokens,
}) => {
  return (
    <nav data-qa="filter-row" className="ui5-filter" aria-label="Finding counts">
      <strong style={{ cursor: 'pointer' }} onClick={onOpenProblems} title="View Problems List">
        Problems {analysisExists ? activeFindings.length : 0}
      </strong>
      {isStale && (
        <span className="ui6-badge insecure" style={{ marginLeft: 6 }}>
          Out of date
        </span>
      )}
      {(['All', 'Security', 'Lexical', 'Syntax'] as const).map((filter) => (
        <button
          key={filter}
          className="ui6-chip"
          aria-pressed={tokenMainFilter === filter}
          onClick={() => onSelectTokenMainFilter(filter)}
        >
          {filter}
          {filter === 'Security'
            ? ` ${activeFindings.filter((f) => !['lexical', 'syntax'].includes(f.kind || 'security')).length}`
            : filter === 'Lexical'
              ? ` ${activeFindings.filter((f) => f.kind === 'lexical').length}`
              : filter === 'Syntax'
                ? ` ${activeFindings.filter((f) => f.kind === 'syntax').length}`
                : ''}
        </button>
      ))}
      {(['dangerous', 'suspicious', 'malicious'] as const).map((group) => (
        <button
          key={group}
          className="ui6-chip"
          aria-pressed={tokenGroups.includes(group)}
          onClick={() => onToggleTokenGroup(group)}
        >
          {group[0].toUpperCase() + group.slice(1)}
        </button>
      ))}
      <label className="ui6-show-all">
        <input
          type="checkbox"
          checked={showAllTokens}
          onChange={(event) => onToggleShowAllTokens(event.target.checked)}
        />
        Show all
      </label>
      <span style={{ marginLeft: 'auto' }}>F8 next</span>
    </nav>
  );
};
