import React from 'react';

export type SidebarPane =
  | 'pane-explorer'
  | 'pane-search'
  | 'pane-git'
  | 'pane-debug'
  | 'pane-extensions'
  | 'pane-security'
  | 'pane-pipeline'
  | 'pane-settings';

interface ActivityBarProps {
  activePane: SidebarPane;
  onSelectPane: (pane: SidebarPane) => void;
  securityCount: number;
  hasGitChanges?: boolean;
  onToggleAssistant: () => void;
  assistantOpen: boolean;
}

export const ActivityBar: React.FC<ActivityBarProps> = ({
  activePane,
  onSelectPane,
  securityCount,
  hasGitChanges = true,
  onToggleAssistant,
  assistantOpen,
}) => {
  const getButtonClass = (pane: SidebarPane) => {
    const isActive = activePane === pane;
    return `activity-btn w-9 h-9 rounded-md flex items-center justify-center transition-all relative ${
      isActive
        ? 'text-text-primary bg-surface-selected border-l-2 border-primary shadow-xs'
        : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'
    }`;
  };

  return (
    <aside className="w-[50px] bg-surface-deepest border-r border-border-primary flex flex-col items-center justify-between py-2.5 shrink-0 z-40 select-none transition-colors">
      <nav className="flex flex-col items-center gap-1.5 w-full" id="activityBar">
        {/* Explorer */}
        <button
          type="button"
          className={getButtonClass('pane-explorer')}
          onClick={() => onSelectPane('pane-explorer')}
          title="Explorer (Project Files)"
          data-pane="pane-explorer"
        >
          <span className="material-symbols-outlined text-[19px]">folder</span>
        </button>

        {/* Search & Replace */}
        <button
          type="button"
          className={getButtonClass('pane-search')}
          onClick={() => onSelectPane('pane-search')}
          title="Search & Replace (Regex / BOM)"
          data-pane="pane-search"
        >
          <span className="material-symbols-outlined text-[19px]">search</span>
        </button>

        {/* Git Source Control */}
        <button
          type="button"
          className={getButtonClass('pane-git')}
          onClick={() => onSelectPane('pane-git')}
          title="Source Control (Git)"
          data-pane="pane-git"
        >
          <span className="material-symbols-outlined text-[19px]">source_environment</span>
          {hasGitChanges && (
            <span className="w-1.5 h-1.5 rounded-full bg-status-warning absolute top-1.5 right-1.5" />
          )}
        </button>

        {/* Run & Debug */}
        <button
          type="button"
          className={getButtonClass('pane-debug')}
          onClick={() => onSelectPane('pane-debug')}
          title="Run & Debug"
          data-pane="pane-debug"
        >
          <span className="material-symbols-outlined text-[19px]">play_arrow</span>
        </button>

        {/* Extensions */}
        <button
          type="button"
          className={getButtonClass('pane-extensions')}
          onClick={() => onSelectPane('pane-extensions')}
          title="Extensions Marketplace"
          data-pane="pane-extensions"
        >
          <span className="material-symbols-outlined text-[19px]">extension</span>
        </button>

        {/* Security Center */}
        <button
          type="button"
          className={getButtonClass('pane-security')}
          onClick={() => onSelectPane('pane-security')}
          title="Security Center (Trojan / CVE Audit)"
          data-pane="pane-security"
        >
          <span className="material-symbols-outlined text-[19px] text-status-warning">shield</span>
          {securityCount > 0 && (
            <span className="px-1 rounded-full bg-status-error text-white font-bold text-[9px] absolute top-1 right-1 leading-none py-0.5">
              {securityCount}
            </span>
          )}
        </button>

        {/* Agent Pipeline */}
        <button
          type="button"
          className={getButtonClass('pane-pipeline')}
          onClick={() => onSelectPane('pane-pipeline')}
          title="Agent Swarm Pipeline Graph"
          data-pane="pane-pipeline"
        >
          <span className="material-symbols-outlined text-[19px]">hub</span>
        </button>

        {/* AI Assistant Toggle */}
        <button
          type="button"
          className={`activity-btn w-9 h-9 rounded-md flex items-center justify-center hover:text-text-primary hover:bg-surface-hover transition-all relative ${
            assistantOpen ? 'text-accent-ai bg-surface-selected' : 'text-accent-ai'
          }`}
          id="btnRailAssistantToggle"
          onClick={onToggleAssistant}
          title="Toggle AI Assistant Panel"
        >
          <span className="material-symbols-outlined text-[19px]">smart_toy</span>
          <span className="w-1.5 h-1.5 rounded-full bg-accent-ai absolute top-1.5 right-1.5" />
        </button>
      </nav>

      {/* Bottom Preferences / Settings */}
      <div className="flex flex-col items-center gap-1 w-full">
        <button
          type="button"
          className={getButtonClass('pane-settings')}
          onClick={() => onSelectPane('pane-settings')}
          title="IDE Preferences"
          data-pane="pane-settings"
        >
          <span className="material-symbols-outlined text-[19px]">settings</span>
        </button>
      </div>
    </aside>
  );
};

