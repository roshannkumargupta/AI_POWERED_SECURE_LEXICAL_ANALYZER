import React, { useState, useEffect } from 'react';
import type { AIGenerateResponse } from '../../api/client';

export type SupportedLanguage = 'cpp' | 'python' | 'java' | 'javascript';

interface BuildWithAiModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeLanguage?: string;
  onGenerate: (language: SupportedLanguage, requirement: string) => Promise<AIGenerateResponse | null>;
  onInsertIntoEditor: (code: string) => void;
  onCreateFile: (fileName: string, content: string) => Promise<void>;
  onRefineInAssistant: (candidateCode: string, requirement: string) => void;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
}

export const BuildWithAiModal: React.FC<BuildWithAiModalProps> = ({
  isOpen,
  onClose,
  activeLanguage = 'cpp',
  onGenerate,
  onInsertIntoEditor,
  onCreateFile,
  onRefineInAssistant,
  onShowToast,
}) => {
  const [selectedLang, setSelectedLang] = useState<SupportedLanguage>('cpp');
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [candidate, setCandidate] = useState<AIGenerateResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'code' | 'checklist'>('code');
  const [newFileName, setNewFileName] = useState('');
  const [isCreatingFile, setIsCreatingFile] = useState(false);

  useEffect(() => {
    const l = activeLanguage.toLowerCase();
    if (l.includes('python')) setSelectedLang('python');
    else if (l.includes('java') && !l.includes('script')) setSelectedLang('java');
    else if (l.includes('javascript') || l.includes('js')) setSelectedLang('javascript');
    else setSelectedLang('cpp');
  }, [activeLanguage]);

  useEffect(() => {
    if (candidate) {
      const ext =
        selectedLang === 'cpp'
          ? 'cpp'
          : selectedLang === 'python'
          ? 'py'
          : selectedLang === 'java'
          ? 'java'
          : 'js';
      setNewFileName(`generated_${Date.now().toString().slice(-4)}.${ext}`);
    }
  }, [candidate, selectedLang]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isGenerating) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isGenerating, onClose]);

  if (!isOpen) return null;

  const handleExecuteGenerate = async () => {
    if (!prompt.trim() || isGenerating) return;
    setIsGenerating(true);
    try {
      const result = await onGenerate(selectedLang, prompt.trim());
      if (result) {
        setCandidate(result);
        onShowToast('Candidate code generated successfully via Groq.', 'success');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyCode = () => {
    if (!candidate?.code) return;
    void navigator.clipboard.writeText(candidate.code);
    onShowToast('Generated code copied to clipboard!', 'success');
  };

  const handleInsert = () => {
    if (!candidate?.code) return;
    onInsertIntoEditor(candidate.code);
    onShowToast('Inserted candidate code into active editor.', 'success');
    onClose();
  };

  const handleCreateFile = async () => {
    if (!candidate?.code || !newFileName.trim()) return;
    setIsCreatingFile(true);
    try {
      await onCreateFile(newFileName.trim(), candidate.code);
      onShowToast(`File ${newFileName.trim()} created in workspace.`, 'success');
      onClose();
    } catch (err: any) {
      onShowToast(`Failed to create file: ${err?.message || 'Error'}`, 'error');
    } finally {
      setIsCreatingFile(false);
    }
  };

  const handleRefine = () => {
    if (!candidate?.code) return;
    onRefineInAssistant(candidate.code, prompt);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-surface-deepest/80 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-in fade-in"
      id="buildAiModal"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isGenerating) onClose();
      }}
    >
      <div className="bg-surface-elevated border border-border-primary rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-4 py-3 bg-surface-deepest border-b border-border-subtle flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-accent-ai text-[19px]">auto_awesome</span>
            <span className="font-semibold text-text-primary text-[13px]">Build / Generate with AI</span>
            <span className="px-1.5 py-0.2 rounded bg-accent-ai/20 text-accent-ai border border-accent-ai/30 text-[10px] font-mono">
              Groq Cloud
            </span>
          </div>
          <button
            type="button"
            className="text-text-muted hover:text-text-primary p-1 rounded hover:bg-surface-hover transition-colors"
            onClick={onClose}
            disabled={isGenerating}
          >
            <span className="material-symbols-outlined text-[17px]">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 overflow-y-auto flex-1">
          {!candidate ? (
            <>
              {/* Language Selection */}
              <div>
                <label className="text-[11px] text-text-muted block mb-1.5 font-semibold uppercase tracking-wider">
                  Select Target Language
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {(
                    [
                      { id: 'cpp', name: 'C++', ext: '.cpp' },
                      { id: 'python', name: 'Python', ext: '.py' },
                      { id: 'java', name: 'Java', ext: '.java' },
                      { id: 'javascript', name: 'JavaScript', ext: '.js' },
                    ] as const
                  ).map((lang) => (
                    <button
                      key={lang.id}
                      type="button"
                      className={`px-3 py-2 rounded-lg border text-left transition-all ${
                        selectedLang === lang.id
                          ? 'border-primary bg-primary/10 text-primary font-semibold shadow-xs'
                          : 'border-border-subtle bg-surface-deepest text-text-secondary hover:border-border-primary'
                      }`}
                      onClick={() => setSelectedLang(lang.id)}
                    >
                      <div className="text-[12px]">{lang.name}</div>
                      <div className="text-[10px] text-text-muted font-mono">{lang.ext}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Template Buttons */}
              <div>
                <label className="text-[11px] text-text-muted block mb-1.5 font-semibold uppercase tracking-wider">
                  Target Templates
                </label>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <button
                    type="button"
                    className="p-2 rounded-lg bg-surface-deepest border border-border-subtle text-left hover:border-primary transition-colors shadow-xs"
                    onClick={() =>
                      setPrompt(
                        'Generate a secure tokenizer for arithmetic operators with integer overflow boundary checks.'
                      )
                    }
                  >
                    <div className="font-semibold text-text-primary">Arithmetic Tokenizer</div>
                    <div className="text-text-muted text-[10px]">Includes integer boundary checks</div>
                  </button>
                  <button
                    type="button"
                    className="p-2 rounded-lg bg-surface-deepest border border-border-subtle text-left hover:border-primary transition-colors shadow-xs"
                    onClick={() =>
                      setPrompt(
                        'Generate a Unicode sanitizer function stripping Zero-Width and Bidi Trojan characters (U+FEFF, U+202E).'
                      )
                    }
                  >
                    <div className="font-semibold text-text-primary">Unicode Sanitizer</div>
                    <div className="text-text-muted text-[10px]">Strips U+FEFF, U+202E, RTL tokens</div>
                  </button>
                </div>
              </div>

              {/* Prompt Textarea */}
              <div>
                <label className="text-[11px] text-text-muted block mb-1 font-semibold uppercase tracking-wider">
                  Describe Requirements
                </label>
                <textarea
                  className="w-full bg-surface-deepest border border-border-primary rounded-lg p-2.5 text-[12px] text-text-primary placeholder-text-muted outline-none focus:border-primary resize-none font-mono"
                  id="buildAiInput"
                  placeholder="Describe the code, algorithmic logic or lexer rules to generate..."
                  rows={4}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                />
              </div>
            </>
          ) : (
            /* Candidate Code View */
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-border-subtle pb-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-status-success" />
                  <span className="text-[12px] font-semibold text-text-primary">Generated Candidate</span>
                  <span className="text-[10px] font-mono text-text-muted px-1.5 py-0.5 rounded bg-surface-deepest border border-border-subtle uppercase">
                    {candidate.language}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    className={`px-2.5 py-1 text-[11px] rounded transition-colors ${
                      activeTab === 'code'
                        ? 'bg-primary text-white font-semibold'
                        : 'text-text-secondary hover:bg-surface-hover'
                    }`}
                    onClick={() => setActiveTab('code')}
                  >
                    Code Preview
                  </button>
                  <button
                    type="button"
                    className={`px-2.5 py-1 text-[11px] rounded transition-colors ${
                      activeTab === 'checklist'
                        ? 'bg-primary text-white font-semibold'
                        : 'text-text-secondary hover:bg-surface-hover'
                    }`}
                    onClick={() => setActiveTab('checklist')}
                  >
                    Checklist &amp; Notes
                  </button>
                </div>
              </div>

              {activeTab === 'code' ? (
                <div className="relative">
                  <pre className="bg-surface-deepest border border-border-subtle rounded-lg p-3 text-[11px] font-mono text-text-primary max-h-80 overflow-y-auto leading-relaxed select-text">
                    <code>{candidate.code}</code>
                  </pre>
                </div>
              ) : (
                <div className="space-y-2.5 bg-surface-deepest border border-border-subtle rounded-lg p-3 text-[11px] max-h-80 overflow-y-auto">
                  <div>
                    <div className="font-semibold text-text-primary text-[11px] mb-1">AI Explanation</div>
                    <p className="text-text-secondary leading-relaxed">{candidate.explanation}</p>
                  </div>
                  {candidate.assumptions && candidate.assumptions.length > 0 && (
                    <div className="pt-2 border-t border-border-subtle">
                      <div className="font-semibold text-text-primary text-[11px] mb-1">Assumptions</div>
                      <ul className="list-disc list-inside space-y-0.5 text-text-secondary">
                        {candidate.assumptions.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {candidate.requirements_checklist && candidate.requirements_checklist.length > 0 && (
                    <div className="pt-2 border-t border-border-subtle">
                      <div className="font-semibold text-text-primary text-[11px] mb-1">
                        Requirements Verification
                      </div>
                      <div className="space-y-1">
                        {candidate.requirements_checklist.map((reqItem, idx) => (
                          <div key={idx} className="flex items-start gap-1.5 text-[10px]">
                            <span
                              className={`material-symbols-outlined text-[14px] mt-0.5 ${
                                reqItem.status === 'met' ? 'text-status-success' : 'text-status-warning'
                              }`}
                            >
                              {reqItem.status === 'met' ? 'check_circle' : 'help'}
                            </span>
                            <div>
                              <span className="font-medium text-text-primary">{reqItem.requirement}</span>
                              <span className="text-text-muted ml-1">— {reqItem.evidence}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Create File Option */}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-[11px] text-text-muted font-medium shrink-0">Save as file:</span>
                <input
                  type="text"
                  className="bg-surface-deepest border border-border-primary rounded px-2 py-1 text-[11px] text-text-primary font-mono outline-none focus:border-primary flex-1"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  placeholder="filename.ext"
                />
                <button
                  type="button"
                  className="px-2.5 py-1 bg-surface-container hover:bg-surface-hover text-text-primary rounded text-[11px] font-medium border border-border-subtle transition-colors shrink-0 disabled:opacity-50"
                  onClick={handleCreateFile}
                  disabled={isCreatingFile || !newFileName.trim()}
                >
                  Create File
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-4 py-3 bg-surface-deepest border-t border-border-subtle flex justify-between items-center shrink-0">
          {!candidate ? (
            <>
              <button
                type="button"
                className="px-3 py-1.5 rounded-md text-[11px] text-text-secondary hover:bg-surface-hover transition-colors"
                onClick={onClose}
                disabled={isGenerating}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-4 py-1.5 rounded-md text-[11px] font-semibold bg-accent-ai hover:bg-accent-ai/90 text-white flex items-center gap-1.5 shadow-xs transition-colors disabled:opacity-50"
                onClick={handleExecuteGenerate}
                disabled={isGenerating || !prompt.trim()}
              >
                <span className={`material-symbols-outlined text-[14px] ${isGenerating ? 'animate-spin' : ''}`}>
                  {isGenerating ? 'sync' : 'bolt'}
                </span>
                <span>{isGenerating ? 'Generating...' : 'Generate Code'}</span>
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="px-3 py-1.5 rounded-md text-[11px] text-text-secondary hover:bg-surface-hover transition-colors flex items-center gap-1"
                onClick={() => setCandidate(null)}
              >
                <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                <span>Edit Prompt</span>
              </button>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="px-2.5 py-1.5 rounded-md text-[11px] text-status-error bg-status-error/10 hover:bg-status-error/20 border border-status-error/30 transition-colors flex items-center gap-1"
                  onClick={() => {
                    setCandidate(null);
                    onClose();
                    onShowToast('Generated code candidate rejected.', 'info');
                  }}
                  title="Reject and discard candidate code"
                >
                  <span className="material-symbols-outlined text-[14px]">cancel</span>
                  <span>Reject</span>
                </button>
                <button
                  type="button"
                  className="px-2.5 py-1.5 rounded-md text-[11px] text-text-primary bg-surface-container hover:bg-surface-hover border border-border-subtle transition-colors flex items-center gap-1"
                  onClick={handleCopyCode}
                  title="Copy Code"
                >
                  <span className="material-symbols-outlined text-[14px]">content_copy</span>
                  <span>Copy</span>
                </button>
                <button
                  type="button"
                  className="px-2.5 py-1.5 rounded-md text-[11px] text-accent-ai bg-accent-ai/10 hover:bg-accent-ai/20 border border-accent-ai/30 transition-colors flex items-center gap-1"
                  onClick={handleRefine}
                  title="Refine in Assistant"
                >
                  <span className="material-symbols-outlined text-[14px]">auto_fix_high</span>
                  <span>Refine in Chat</span>
                </button>
                <button
                  type="button"
                  className="px-3.5 py-1.5 rounded-md text-[11px] font-semibold bg-primary hover:bg-primary/90 text-white flex items-center gap-1 shadow-xs transition-colors"
                  onClick={handleInsert}
                >
                  <span className="material-symbols-outlined text-[14px]">input</span>
                  <span>Insert into Editor</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
