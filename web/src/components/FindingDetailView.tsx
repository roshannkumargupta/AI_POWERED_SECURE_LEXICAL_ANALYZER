import React from 'react';
import { CheckCircle2, Flag, GitBranch, Sparkles, EyeOff } from 'lucide-react';
import { Finding, Fix, TaintPathStep } from '../api/client';
import { TaintPath } from './TaintPath';
import { FixCard } from './FixCard';
import { SeverityBadge } from './SeverityBadge';
import { FindingExplanation } from './FindingExplanation';
import {
  findingContainerStyle,
  findingHeaderStyle,
  ruleCodeStyle,
  titleStyle,
  locationSubStyle,
  sectionBoxStyle,
  sectionTitleStyle,
  flowToggleBtnStyle,
  reviewFixBtnStyle,
  feedbackBtnStyle,
  noFindingStyle,
} from './findingStyles';

interface FindingDetailViewProps {
  selectedFinding: Finding | null;
  isDataFlowActive: boolean;
  onToggleDataFlow: (findingId: string) => void;
  onJumpToStep: (step: TaintPathStep) => void;
  onApplyFix: (fix: Fix, finding: Finding) => void;
  onOpenDiff: (fix: Fix, finding: Finding) => void;
  onMarkFalsePositive: (finding: Finding) => void;
  onSuppressFinding?: (finding: Finding) => void;
  onAskAIFix?: (finding: Finding) => void;
  isAskingAI?: boolean;
  llmConfigured?: boolean;
  llmProvider?: string;
}

export const FindingDetailView: React.FC<FindingDetailViewProps> = ({
  selectedFinding,
  isDataFlowActive,
  onToggleDataFlow,
  onJumpToStep,
  onApplyFix,
  onOpenDiff,
  onMarkFalsePositive,
  onSuppressFinding,
  onAskAIFix,
  isAskingAI = false,
  llmConfigured = false,
  llmProvider = 'none',
}) => {
  if (!selectedFinding) {
    return (
      <div style={noFindingStyle}>
        <CheckCircle2 size={32} color="var(--muted)" />
        <p style={{ marginTop: '12px', color: 'var(--muted)', fontSize: '13px' }}>
          Select a problem from the bottom panel or click a code squiggle to view vulnerability
          analysis.
        </p>
      </div>
    );
  }

  return (
    <div style={findingContainerStyle}>
      <div style={findingHeaderStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <SeverityBadge severity={selectedFinding.severity} />
          <code style={ruleCodeStyle}>{selectedFinding.rule_id}</code>
        </div>
        <h3 style={titleStyle}>{selectedFinding.title}</h3>
        <span style={locationSubStyle}>
          {selectedFinding.cwe} · {selectedFinding.message}
        </span>
      </div>

      <FindingExplanation finding={selectedFinding} />

      {/* Data Flow Section */}
      {selectedFinding.taint_path && selectedFinding.taint_path.length > 0 && (
        <div style={sectionBoxStyle}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={sectionTitleStyle}>Taint Flow Analysis</span>
            <button
              style={{
                ...flowToggleBtnStyle,
                backgroundColor: isDataFlowActive ? 'var(--accent)' : 'var(--panel-2)',
                color: isDataFlowActive ? 'var(--text-on-accent)' : 'var(--text-secondary)',
              }}
              onClick={() => onToggleDataFlow(selectedFinding.id)}
            >
              <GitBranch size={13} />
              {isDataFlowActive ? 'Hide Flow' : 'Show Flow in Editor'}
            </button>
          </div>
          <TaintPath steps={selectedFinding.taint_path} onJumpToStep={onJumpToStep} />
        </div>
      )}

      {/* Automated Fixes Section */}
      <div style={sectionBoxStyle}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span style={sectionTitleStyle}>
            {selectedFinding.fixes && selectedFinding.fixes.length > 0
              ? 'Suggested Fixes'
              : 'Rule Advice'}
          </span>
          <button
            data-qa="ask-ai-fix-btn"
            disabled={!llmConfigured || isAskingAI}
            title={
              llmConfigured
                ? `Ask AI (${llmProvider}) for alternative fix`
                : 'Add GROQ_API_KEY to your .env file and restart'
            }
            style={{
              ...reviewFixBtnStyle,
              opacity: llmConfigured ? 1 : 0.55,
              cursor: llmConfigured ? 'pointer' : 'not-allowed',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
            }}
            onClick={() => onAskAIFix?.(selectedFinding)}
          >
            <Sparkles size={12} />
            {isAskingAI ? 'Asking AI...' : 'Ask AI for another fix'}
          </button>
        </div>

        {selectedFinding.fixes && selectedFinding.fixes.length > 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              marginTop: '6px',
            }}
          >
            {selectedFinding.fixes.map((fix) => (
              <FixCard
                key={fix.id}
                fix={fix}
                finding={selectedFinding}
                onOpenDiff={onOpenDiff}
                onApplyFix={onApplyFix}
              />
            ))}
          </div>
        ) : (
          <div
            style={{
              marginTop: '6px',
              fontSize: 11,
              color: 'var(--text-secondary)',
              lineHeight: 1.4,
            }}
          >
            <p style={{ margin: '0 0 6px', fontStyle: 'italic' }}>
              No automatic rule fix for this issue.
            </p>
          </div>
        )}
      </div>

      <details style={{ marginTop: 'auto' }}>
        <summary style={{ cursor: 'pointer', color: 'var(--muted)', fontSize: 11 }}>
          More actions
        </summary>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
            marginTop: '6px',
          }}
        >
          <button
            data-qa="suppress-finding-btn"
            style={feedbackBtnStyle}
            onClick={() => onSuppressFinding?.(selectedFinding)}
            title="Insert inline suppression comment in code"
          >
            <EyeOff size={13} /> Suppress this finding
          </button>
          <button style={feedbackBtnStyle} onClick={() => onMarkFalsePositive(selectedFinding)}>
            <Flag size={13} /> Mark as False Positive
          </button>
        </div>
      </details>
    </div>
  );
};
