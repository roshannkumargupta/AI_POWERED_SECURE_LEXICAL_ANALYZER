import React from 'react';

interface AIExplainViewProps {
  explanationText?: string;
  onAskFollowUp: (prompt: string) => void;
}

export const AIExplainView: React.FC<AIExplainViewProps> = ({
  explanationText,
  onAskFollowUp,
}) => {
  const defaultText =
    'Select a token, syntax diagnostic, or security finding and click "Explain" to generate a verified explanation based on recorded compiler diagnostics and AI evidence.';

  return (
    <div
      className="panel-view flex-1 flex flex-col min-w-0 border-r border-border-primary overflow-hidden p-3 space-y-2.5"
      id="view-ai-explain"
    >
      <div className="font-semibold text-text-primary flex items-center gap-1.5">
        <span className="material-symbols-outlined text-accent-ai text-[18px]">psychology</span> AI Deep Lexical
        Explanation
      </div>
      <div className="p-3 bg-surface-elevated rounded-lg border border-border-subtle text-[11px] space-y-2 text-text-secondary leading-relaxed shadow-xs">
        <p>{explanationText || defaultText}</p>
        <button
          type="button"
          className="px-3 py-1 bg-primary text-white rounded-md text-[11px] font-semibold shadow-xs hover:bg-primary/90 transition-colors"
          onClick={() =>
            onAskFollowUp('Can you explain the Trojan Source attack vector in depth?')
          }
        >
          Ask follow-up in Assistant
        </button>
      </div>
    </div>
  );
};

