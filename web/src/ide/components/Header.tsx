import React, { useState, useRef, useEffect } from 'react';

interface HeaderProps {
  version: string;
  engineMode: 'local' | 'groq';
  onToggleEngine: () => void;
  securityAlertCount: number;
  onOpenSecurity: () => void;
  resolvedTheme: 'dark' | 'light';
  onToggleTheme: () => void;
  assistantOpen: boolean;
  onToggleAssistant: () => void;
  onOpenCommandPalette?: () => void;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
}

export const Header: React.FC<HeaderProps> = ({
  version,
  engineMode,
  onToggleEngine,
  securityAlertCount,
  onOpenSecurity,
  resolvedTheme,
  onToggleTheme,
  assistantOpen,
  onToggleAssistant,
  onOpenCommandPalette,
  onShowToast,
}) => {
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserDropdownOpen(false);
      }
    };
    document.addEventListener('pointerdown', handleClickOutside);
    return () => document.removeEventListener('pointerdown', handleClickOutside);
  }, []);

  return (
    <header className="h-[48px] w-full bg-surface-deepest border-b border-border-primary flex items-center justify-between px-3 shrink-0 z-50 transition-colors shadow-xs">
      <div className="flex items-center gap-3">
        {/* Brand Logo / Badge */}
        <div
          className="flex items-center gap-2 group cursor-pointer"
          onClick={() => onShowToast(`SecureLex IDE Core v${version} active · Engine Ready`)}
        >
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-primary-hover flex items-center justify-center text-white shadow-sm ring-1 ring-white/20 group-hover:scale-105 transition-transform">
            <span className="material-symbols-outlined text-[17px]">shield</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-[13px] tracking-tight text-text-primary">
                SecureLex<span className="text-primary font-mono ml-0.5 font-normal">IDE</span>
              </span>
              <span className="px-1.5 py-0.5 rounded bg-primary/15 text-primary text-[10px] font-mono font-semibold border border-primary/30 leading-none">
                v{version}
              </span>
            </div>
          </div>
        </div>
        <div className="h-4 w-[1px] bg-border-primary hidden xl:block" />
        <span className="text-[11px] text-text-secondary hidden xl:inline font-medium tracking-tight">
          AI-Powered Secure Lexical Analyzer &amp; AST Engine
        </span>
      </div>

      {/* Center Command Palette Quick Search Bar */}
      {onOpenCommandPalette && (
        <div
          className="flex items-center gap-2 px-3 py-1 bg-surface-elevated/80 border border-border-primary rounded-md cursor-pointer hover:border-primary/60 hover:bg-surface-hover transition-colors text-[11px] text-text-muted font-sans w-64 max-w-sm hidden sm:flex shadow-xs"
          onClick={onOpenCommandPalette}
          title="Open Command Palette (Ctrl+Shift+P / F1)"
        >
          <span className="material-symbols-outlined text-[15px]">terminal</span>
          <span className="flex-1 truncate">Type a command or file...</span>
          <kbd className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-surface-deepest border border-border-subtle">
            Ctrl+Shift+P
          </kbd>
        </div>
      )}

      {/* Right Controls */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border-primary text-[11px] transition-all shadow-xs ${
            assistantOpen
              ? 'bg-surface-selected text-text-primary border-primary/40'
              : 'bg-surface-container text-text-secondary hover:bg-surface-hover hover:text-text-primary'
          }`}
          id="btnToggleAssistantHeader"
          onClick={onToggleAssistant}
          title="Toggle AI Assistant (Ctrl/⌘+B)"
        >
          <span className="material-symbols-outlined text-[15px] text-accent-ai">smart_toy</span>
          <span className="font-medium hidden sm:inline">Assistant</span>
        </button>

        {/* Engine Switcher */}
        <button
          type="button"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-container border border-border-primary hover:bg-surface-hover hover:border-text-muted/40 text-[11px] transition-all shadow-xs"
          id="btnEngineToggle"
          title="Toggle Execution Engine"
          onClick={onToggleEngine}
        >
          <span
            className={`w-2 h-2 rounded-full shadow-sm animate-pulse ${
              engineMode === 'local' ? 'bg-status-success' : 'bg-primary'
            }`}
            id="engineDot"
          />
          <span className="font-semibold text-text-primary" id="engineLabel">
            {engineMode === 'local' ? 'Local Engine' : 'Groq Cloud'}
          </span>
          <span className="text-[10px] text-text-muted font-mono ml-0.5 hidden sm:inline">
            {engineMode === 'local' ? '0ms' : 'Fast'}
          </span>
        </button>

        {/* Groq Remote Mode Button */}
        <button
          type="button"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-container/60 hover:bg-surface-hover border border-border-primary text-[11px] text-text-secondary hover:text-text-primary transition-all shadow-xs"
          id="btnGroqDirect"
          title="Groq Remote Inference (Llama 3.3 70B)"
          onClick={() => onShowToast('Groq Cloud (Llama 3.3 70B) active and connected', 'success')}
        >
          <span className="material-symbols-outlined text-[15px] text-primary">cloud</span>
          <span className="font-medium">Groq Remote</span>
        </button>

        {/* Security Quick Alert Pill */}
        <button
          type="button"
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all shadow-xs ${
            securityAlertCount > 0
              ? 'bg-status-warning/15 text-status-warning hover:bg-status-warning/25 border border-status-warning/40'
              : 'bg-surface-container text-text-secondary border border-border-primary hover:bg-surface-hover'
          }`}
          id="btnHeaderSecurityAlert"
          title={`Security Center: ${securityAlertCount} Active Vulnerabilities`}
          onClick={onOpenSecurity}
        >
          <span className="material-symbols-outlined text-[15px]">
            {securityAlertCount > 0 ? 'report' : 'shield'}
          </span>
          <span>{securityAlertCount > 0 ? `${securityAlertCount} Alert` : 'Clean'}</span>
        </button>

        {/* Theme Switcher */}
        <button
          type="button"
          aria-label={resolvedTheme === 'dark' ? 'Light' : 'Dark'}
          className="w-7 h-7 rounded-md flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-surface-hover border border-border-primary transition-colors"
          id="btnThemeToggle"
          title="Toggle Dark / Clean Light Mode"
          onClick={onToggleTheme}
        >
          <span className="material-symbols-outlined text-[17px]" id="themeIcon">
            {resolvedTheme === 'dark' ? 'dark_mode' : 'light_mode'}
          </span>
          <span className="sr-only">{resolvedTheme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>

        {/* User Profile Dropdown */}
        <div className="relative" ref={userMenuRef}>
          <button
            type="button"
            className="w-7 h-7 rounded-full bg-gradient-to-tr from-accent-ai to-primary text-white flex items-center justify-center font-bold text-[11px] ring-2 ring-accent-ai/30 hover:ring-accent-ai/70 transition-all shadow-sm"
            id="btnUserMenu"
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
          >
            <span>R</span>
          </button>
          {userDropdownOpen && (
            <div
              className="absolute right-0 top-full mt-1.5 w-52 bg-surface-elevated border border-border-primary rounded-lg shadow-2xl py-1 z-50"
              id="userDropdown"
            >
              <div className="px-3 py-2 border-b border-border-subtle bg-surface-deepest/50">
                <div className="font-semibold text-text-primary text-[12px]">DevSecOps Lead</div>
                <div className="text-[10px] text-text-muted font-mono">dev@securelex.corp</div>
              </div>
              <button
                type="button"
                className="w-full text-left px-3 py-1.5 hover:bg-surface-hover text-text-secondary hover:text-text-primary flex items-center gap-2 transition-colors text-[11px]"
                onClick={() => {
                  setUserDropdownOpen(false);
                  onShowToast('Profile: DevSecOps Lead');
                }}
              >
                <span className="material-symbols-outlined text-[15px] text-primary">badge</span> Profile Info
              </button>
              <button
                type="button"
                className="w-full text-left px-3 py-1.5 hover:bg-surface-hover text-text-secondary hover:text-text-primary flex items-center gap-2 transition-colors text-[11px]"
                onClick={() => {
                  setUserDropdownOpen(false);
                  onShowToast('Groq Cloud API Key Configured on Backend', 'success');
                }}
              >
                <span className="material-symbols-outlined text-[15px] text-accent-ai">key</span> Groq API Key
              </button>
              <button
                type="button"
                className="w-full text-left px-3 py-1.5 hover:bg-surface-hover text-text-secondary hover:text-text-primary flex items-center gap-2 border-t border-border-subtle transition-colors text-[11px]"
                onClick={() => {
                  setUserDropdownOpen(false);
                  onShowToast('Session active in offline/local workbench mode', 'info');
                }}
              >
                <span className="material-symbols-outlined text-[15px] text-status-error">logout</span> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
