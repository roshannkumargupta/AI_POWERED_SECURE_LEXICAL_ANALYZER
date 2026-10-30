import React, { useState, useRef, useEffect } from 'react';
import type { PatchProposal } from '../../api/client';
import type { EnrichedPatchProposal } from '../patch/patchWorkflow';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  codeSnippets?: string[];
  diff?: {
    file: string;
    delLine?: string;
    addLine?: string;
    unifiedDiff?: string;
  };
  proposal?: PatchProposal | EnrichedPatchProposal;
  targetContext?: {
    file?: string;
    stage?: string;
    findingTitle?: string;
    line?: number;
    col?: number;
  };
  timestamp?: number;
}

interface AssistantPanelProps {
  isOpen: boolean;
  onClose: () => void;
  width?: number;
  onResizeStart?: (e: React.PointerEvent) => void;
  activeFileName: string;
  sourceVersion?: number;
  language?: string;
  cursorLine: number;
  cursorCol: number;
  providerName?: string;
  providerConfigured?: boolean;
  remoteConsented?: boolean;
  onToggleConsent?: () => void;
  contextStage?: string;
  contextFinding?: { title: string; line: number; col: number; id?: string } | null;
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  onNewConversation?: () => void;
  onClearChat: () => void;
  onAcceptDiff?: (proposal?: PatchProposal | EnrichedPatchProposal) => void;
  onRejectDiff?: (proposal?: PatchProposal | EnrichedPatchProposal) => void;
  onImproveDiff?: (proposal?: PatchProposal | EnrichedPatchProposal) => void;
  onReanalyze?: () => void;
  onInsertCodeSnippet?: (code: string) => void;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
  isSending?: boolean;
}

export const AssistantPanel: React.FC<AssistantPanelProps> = ({
  isOpen,
  onClose,
  width = 447,
  onResizeStart,
  activeFileName,
  sourceVersion = 1,
  language = 'cpp',
  cursorLine,
  cursorCol,
  providerName = 'Groq Cloud (openai/gpt-oss-120b)',
  providerConfigured = true,
  remoteConsented = false,
  onToggleConsent,
  contextStage = 'Lexical Scanner',
  contextFinding = null,
  messages,
  onSendMessage,
  onNewConversation,
  onClearChat,
  onAcceptDiff,
  onRejectDiff,
  onImproveDiff,
  onReanalyze,
  onInsertCodeSnippet,
  onShowToast,
  isSending = false,
}) => {
  const [input, setInput] = useState('');
  const [copiedSnippetIdx, setCopiedSnippetIdx] = useState<string | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isSending]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleInsertToken = () => {
    setInput((prev) => `${prev} [Token: <= (U+FEFF)] `);
  };

  const handleInsertTemplate = () => {
    setInput('Verify if this file contains bidirectional Trojan Source overrides (CVE-2021-42574).');
  };

  const handleCopyText = (text: string, id: string) => {
    void navigator.clipboard.writeText(text);
    setCopiedSnippetIdx(id);
    onShowToast('Code copied to clipboard!', 'success');
    setTimeout(() => {
      setCopiedSnippetIdx(null);
    }, 2000);
  };

  // Helper to parse markdown code blocks ```lang ... ```
  const renderMessageContent = (msg: ChatMessage) => {
    const rawText = msg.text || '';
    const parts = rawText.split(/(```[\s\S]*?```)/g);

    return (
      <div className="space-y-2 text-text-primary">
        {parts.map((part, index) => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const lines = part.slice(3, -3).trim().split('\n');
            const maybeLang = lines[0].trim().toLowerCase();
            const hasLang = /^[a-z0-9+#_.-]+$/.test(maybeLang);
            const langTag = hasLang ? maybeLang : language;
            const codeBody = hasLang ? lines.slice(1).join('\n') : lines.join('\n');
            const snippetId = `${msg.id}-block-${index}`;

            return (
              <div
                key={index}
                className="my-2 rounded-lg bg-surface-deepest border border-border-primary overflow-hidden shadow-xs font-mono text-[11px]"
              >
                <div className="px-3 py-1 bg-surface-elevated/80 border-b border-border-subtle flex items-center justify-between text-[10px] text-text-muted">
                  <span className="font-semibold uppercase tracking-wider">{langTag}</span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      className="px-2 py-0.5 rounded hover:bg-surface-hover text-text-secondary hover:text-text-primary transition-colors flex items-center gap-1"
                      onClick={() => handleCopyText(codeBody, snippetId)}
                      title="Copy code"
                    >
                      <span className="material-symbols-outlined text-[13px]">
                        {copiedSnippetIdx === snippetId ? 'check' : 'content_copy'}
                      </span>
                      <span>{copiedSnippetIdx === snippetId ? 'Copied' : 'Copy'}</span>
                    </button>
                    {onInsertCodeSnippet && (
                      <button
                        type="button"
                        className="px-2 py-0.5 rounded hover:bg-surface-hover text-primary hover:underline transition-colors flex items-center gap-1"
                        onClick={() => {
                          onInsertCodeSnippet(codeBody);
                          onShowToast('Code snippet inserted into active editor.', 'success');
                        }}
                        title="Insert at editor cursor"
                      >
                        <span className="material-symbols-outlined text-[13px]">input</span>
                        <span>Insert</span>
                      </button>
                    )}
                  </div>
                </div>
                <pre className="p-3 overflow-x-auto text-text-primary leading-relaxed select-text">
                  <code>{codeBody}</code>
                </pre>
              </div>
            );
          }

          // Plain text paragraph
          return (
            <p key={index} className="leading-relaxed whitespace-pre-wrap">
              {part}
            </p>
          );
        })}

        {/* Enriched Unified Diff / Proposed Patch Box */}
        {(msg.diff || msg.proposal) && (
          <div className="diff-box bg-surface-deepest border border-border-subtle rounded-lg p-3 font-mono text-[11px] space-y-2 mt-2 shadow-xs">
            <div className="flex items-center justify-between text-text-muted text-[10px] pb-1 border-b border-border-subtle/60">
              <div className="flex items-center gap-1.5 font-semibold text-text-primary">
                <span className="material-symbols-outlined text-[13px] text-accent-ai">build_circle</span>
                <span>Proposed Fix: {(msg.proposal as any)?.target_file || msg.diff?.file || activeFileName}</span>
              </div>
              <div className="flex items-center gap-1">
                {msg.proposal?.source_version && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-elevated text-text-secondary border border-border-subtle font-mono">
                    v{msg.proposal.source_version}
                  </span>
                )}
                {msg.proposal?.origin && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-accent-ai/10 text-accent-ai font-semibold uppercase tracking-wider">
                    {msg.proposal.origin}
                  </span>
                )}
              </div>
            </div>

            {/* Related Finding context if available */}
            {(msg.proposal as any)?.finding && (
              <div className="text-[10px] bg-status-warning/10 text-status-warning px-2 py-1 rounded border border-status-warning/20 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[12px]">security</span>
                <span><strong>Finding:</strong> {(msg.proposal as any).finding.title}</span>
              </div>
            )}

            {/* Target Source Range */}
            {(msg.proposal as any)?.original_range && (
              <div className="text-[10px] text-text-muted flex items-center gap-2">
                <span><strong>Target Range:</strong> Ln {(msg.proposal as any).original_range.start_line}:{(msg.proposal as any).original_range.start_col} - Ln {(msg.proposal as any).original_range.end_line}:{(msg.proposal as any).original_range.end_col}</span>
              </div>
            )}

            {/* Original vs Replacement preview */}
            {(msg.proposal as any)?.original_text !== undefined && (msg.proposal as any)?.original_text !== '' && (
              <div className="text-[10px] space-y-1">
                <div className="text-status-error/90 bg-status-error/10 px-2 py-0.5 rounded font-mono truncate">
                  - {(msg.proposal as any).original_text}
                </div>
                <div className="text-status-success/90 bg-status-success/10 px-2 py-0.5 rounded font-mono truncate">
                  + {(msg.proposal as any).replacement_text}
                </div>
              </div>
            )}

            {/* Unified diff */}
            {msg.diff?.unifiedDiff ? (
              <pre className="bg-surface-editor/60 border border-border-subtle rounded p-2 text-[10px] overflow-x-auto leading-relaxed max-h-48">
                {msg.diff.unifiedDiff.split('\n').map((line, i) => {
                  let cls = 'text-text-secondary';
                  if (line.startsWith('+') && !line.startsWith('+++')) cls = 'text-status-success font-semibold bg-status-success/10 block px-1 rounded';
                  else if (line.startsWith('-') && !line.startsWith('---')) cls = 'text-status-error font-semibold bg-status-error/10 block px-1 rounded';
                  else if (line.startsWith('@@')) cls = 'text-accent-ai font-semibold';
                  return (
                    <span key={i} className={cls}>
                      {line}
                      {'\n'}
                    </span>
                  );
                })}
              </pre>
            ) : null}

            {/* Explanation / Rationale */}
            {((msg.proposal as any)?.explanation || msg.proposal?.rationale) && (
              <p className="text-[10px] text-text-secondary italic">
                ℹ️ {(msg.proposal as any)?.explanation || msg.proposal?.rationale}
              </p>
            )}

            {/* Action buttons */}
            <div className="flex items-center gap-1.5 pt-2 border-t border-border-subtle flex-wrap" id="diffActionsRow">
              <button
                type="button"
                className="px-2.5 py-1 bg-status-success text-white rounded text-[11px] font-semibold hover:bg-status-success/90 transition-colors shadow-xs flex items-center gap-1"
                onClick={() => onAcceptDiff?.(msg.proposal)}
              >
                <span className="material-symbols-outlined text-[13px]">check</span>
                <span>Accept &amp; Apply</span>
              </button>
              <button
                type="button"
                className="px-2.5 py-1 bg-surface-container hover:bg-surface-hover text-text-secondary rounded text-[11px] border border-border-subtle transition-colors"
                onClick={() => onRejectDiff?.(msg.proposal)}
              >
                Reject
              </button>
              <button
                type="button"
                className="px-2.5 py-1 bg-surface-container hover:bg-surface-hover text-accent-ai rounded text-[11px] border border-accent-ai/30 transition-colors flex items-center gap-1"
                onClick={() => onImproveDiff?.(msg.proposal)}
              >
                <span className="material-symbols-outlined text-[13px]">auto_fix_high</span>
                <span>Improve with AI</span>
              </button>
            </div>
          </div>
        )}

        {/* If message text offers reanalysis, render interactive Reanalyze Now button */}
        {(msg.text.includes('reanalyze') || msg.text.includes('Reanalysis') || msg.text.includes('outdated')) && onReanalyze && (
          <div className="mt-2 pt-1">
            <button
              type="button"
              className="px-3 py-1.5 bg-primary/10 text-primary border border-primary/30 rounded text-[11px] font-semibold hover:bg-primary/20 transition-colors flex items-center gap-1.5 shadow-xs"
              onClick={onReanalyze}
            >
              <span className="material-symbols-outlined text-[14px]">refresh</span>
              <span>Reanalyze Now</span>
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <aside
      className="bg-surface-explorer flex flex-col shrink-0 h-full overflow-hidden select-none border-l border-border-primary transition-colors relative"
      style={{ width: `${width}px` }}
      id="assistantAside"
    >
      {/* Resizer Handle */}
      {onResizeStart && (
        <div
          className="absolute top-0 left-0 w-1.5 h-full cursor-col-resize hover:bg-primary/40 active:bg-primary z-40 transition-colors"
          onPointerDown={onResizeStart}
          title="Drag to resize Assistant"
        />
      )}
      {/* Header */}
      <div
        className="h-10 px-3 bg-surface-deepest border-b border-border-primary flex items-center justify-between shrink-0 transition-colors"
        id="assistantHeader"
      >
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[19px]">shield</span>
          <span className="font-bold text-[13px] text-text-primary tracking-tight" id="assistantTitleText">
            SecureLex Assistant
          </span>
          <span
            className="px-1.5 py-0.2 rounded bg-accent-ai text-white text-[9px] font-bold tracking-wider"
            id="assistantAiBadge"
          >
            AI
          </span>
        </div>
        <div className="flex items-center gap-1 text-text-muted">
          {onNewConversation && (
            <button
              type="button"
              className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
              onClick={onNewConversation}
              title="New Conversation Thread"
            >
              <span className="material-symbols-outlined text-[16px]">add_comment</span>
            </button>
          )}
          <button
            type="button"
            className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
            onClick={onClearChat}
            title="Clear Chat History"
          >
            <span className="material-symbols-outlined text-[16px]">delete_sweep</span>
          </button>
          <button
            type="button"
            className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
            id="btnCollapseAssistant"
            onClick={onClose}
            title="Collapse Assistant Panel"
          >
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
          </button>
        </div>
      </div>

      {/* Context Bar */}
      <div
        className="px-3 py-1.5 bg-surface-elevated/70 border-b border-border-subtle flex items-center justify-between text-[11px] text-text-secondary shrink-0 transition-colors"
        id="assistantContextBar"
      >
        <div className="flex items-center gap-1.5 truncate">
          <span className="text-text-muted font-medium">Context:</span>
          <span className="font-mono text-text-primary font-semibold" id="assistantFileCtx">
            {activeFileName} (v{sourceVersion})
          </span>
          <span className="text-text-muted">•</span>
          <span className="truncate">{contextStage}</span>
          <span className="text-text-muted">•</span>
          <span className="text-status-error font-medium" id="assistantLineCtx">
            Ln {cursorLine}, Col {cursorCol}
          </span>
        </div>
      </div>

      {/* Context Finding Pill (if attached) */}
      {contextFinding && (
        <div className="px-3 py-1 bg-surface-selected/40 border-b border-border-subtle flex items-center justify-between text-[10px] text-primary">
          <div className="flex items-center gap-1.5 truncate">
            <span className="material-symbols-outlined text-[14px]">bug_report</span>
            <span className="font-semibold truncate">Target: {contextFinding.title}</span>
            <span className="text-text-muted font-mono">(Ln {contextFinding.line}:{contextFinding.col})</span>
          </div>
          <span className="px-1 py-0.2 rounded bg-primary/20 text-primary text-[9px] font-semibold">Attached</span>
        </div>
      )}

      {/* Provider Strip */}
      <div
        className="px-3 py-1 bg-surface-deepest border-b border-border-subtle flex items-center justify-between text-[10px] text-text-muted shrink-0 transition-colors"
        id="assistantProviderStrip"
      >
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              !providerConfigured
                ? 'bg-status-error'
                : remoteConsented
                ? 'bg-status-success'
                : 'bg-status-warning'
            }`}
          />
          <span className="truncate">
            {!providerConfigured
              ? 'Provider: Groq (Not Configured in .env)'
              : `Provider: ${providerName}`}
          </span>
        </div>
        <button
          type="button"
          className="text-primary hover:underline font-mono"
          onClick={onToggleConsent}
          title="Toggle Remote Source Processing Consent"
        >
          {remoteConsented ? 'consent: on' : 'consent: required'}
        </button>
      </div>

      {/* Consent Warning Notice */}
      {!remoteConsented && providerConfigured && (
        <div className="p-2.5 mx-3 mt-2 bg-status-warning/10 border border-status-warning/30 rounded-lg text-[11px] text-status-warning flex items-start gap-2">
          <span className="material-symbols-outlined text-[16px] mt-0.5 shrink-0">info</span>
          <div className="flex-1">
            <span className="font-semibold">Remote Groq processing requires session consent.</span>
            <div className="text-[10px] text-text-secondary mt-0.5">
              Source context will only be sent to Groq when consent is granted.
            </div>
            <button
              type="button"
              className="mt-1.5 px-2 py-0.5 bg-primary text-white rounded text-[10px] font-semibold hover:bg-primary/90 transition-colors"
              onClick={onToggleConsent}
            >
              Grant Session Consent
            </button>
          </div>
        </div>
      )}

      {/* Chat History */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-3 space-y-3.5 select-text text-[12px]"
        id="chatContainer"
      >
        {messages.length === 0 ? (
          <div className="text-center text-text-muted text-[11px] py-6 space-y-2">
            <span className="material-symbols-outlined text-[28px] text-text-muted/60">chat</span>
            <div>No messages yet for this file.</div>
            <div className="text-[10px] text-text-muted/80">
              Ask about lexical tokens, Trojan Source Unicode anomalies, or request an AI fix.
            </div>
          </div>
        ) : (
          messages.map((m) => {
            if (m.sender === 'user') {
              return (
                <div key={m.id} className="flex justify-end gap-2">
                  <div className="chat-user-bubble max-w-[85%] bg-surface-selected text-text-primary px-3 py-2 rounded-lg border border-primary/30 shadow-xs leading-relaxed">
                    {m.text}
                  </div>
                  <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center shrink-0 text-white font-bold text-[10px] shadow-xs">
                    U
                  </div>
                </div>
              );
            }

            return (
              <div key={m.id} className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-full bg-accent-ai flex items-center justify-center shrink-0 mt-0.5 text-white shadow-xs">
                  <span className="material-symbols-outlined text-[14px]">smart_toy</span>
                </div>
                <div className="chat-assistant-card flex-1 bg-surface-elevated border border-border-primary rounded-lg p-3 text-text-primary leading-relaxed shadow-xs space-y-2">
                  {renderMessageContent(m)}
                </div>
              </div>
            );
          })
        )}

        {isSending && (
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full bg-accent-ai flex items-center justify-center shrink-0 mt-0.5 text-white shadow-xs">
              <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
            </div>
            <div className="chat-assistant-card flex-1 bg-surface-elevated border border-border-primary rounded-lg p-3 text-text-muted leading-relaxed shadow-xs flex items-center gap-2">
              <span>Thinking and querying Groq with lexical evidence...</span>
            </div>
          </div>
        )}
      </div>

      {/* Composer */}
      <footer className="p-2.5 bg-surface-deepest border-t border-border-primary shrink-0 transition-colors">
        <form
          className="flex flex-col bg-surface-editor border border-border-primary rounded-lg focus-within:border-primary transition-colors p-2 shadow-xs"
          id="chatForm"
          onSubmit={handleSubmit}
        >
          <textarea
            className="w-full bg-transparent text-text-primary text-[11px] outline-none resize-none placeholder-text-muted leading-relaxed"
            id="chatInput"
            placeholder="Ask anything about this code or prompt an AI fix/improvement..."
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div className="flex items-center justify-between pt-1.5 mt-1 border-t border-border-subtle">
            <div className="flex items-center gap-1 text-text-muted">
              <button
                type="button"
                className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
                onClick={() => onShowToast(`Attached context: ${activeFileName}`)}
                title="Attach Context"
              >
                <span className="material-symbols-outlined text-[15px]">attach_file</span>
              </button>
              <button
                type="button"
                className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
                onClick={handleInsertToken}
                title="Insert Token Reference"
              >
                <span className="material-symbols-outlined text-[15px]">code</span>
              </button>
              <button
                type="button"
                className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
                onClick={handleInsertTemplate}
                title="Prompt Templates"
              >
                <span className="material-symbols-outlined text-[15px]">bolt</span>
              </button>
            </div>
            <button
              type="submit"
              className="flex items-center justify-center p-1.5 bg-primary hover:bg-primary/90 text-white rounded-md transition-colors shadow-xs disabled:opacity-50"
              title="Send Query"
              disabled={isSending || !input.trim()}
            >
              <span className="material-symbols-outlined text-[14px]">send</span>
            </button>
          </div>
        </form>
      </footer>
    </aside>
  );
};
