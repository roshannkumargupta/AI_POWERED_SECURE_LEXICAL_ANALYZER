import React from 'react';
import { Files, FlaskConical, CircleHelp } from 'lucide-react';
import { DocItem } from '../model/doc';
import { FlyoutPanel } from './FlyoutPanel';
import { SampleItem } from '../api/client';
import { ThemeMode, ResolvedTheme } from '../theme/theme';

interface AppActivityStripProps {
  flyout: 'files' | 'samples' | 'help' | null;
  onToggleFlyout: (mode: 'files' | 'samples' | 'help', button: HTMLButtonElement) => void;
  flyoutRef: React.RefObject<HTMLDivElement>;
  openDocs: DocItem[];
  activeDocId: string | null;
  samples: SampleItem[];
  language: string;
  engine: any;
  themeMode: ThemeMode;
  themeResolved: ResolvedTheme;
  onThemeChange: (mode: ThemeMode) => void;
  analyzeWhileTyping: boolean;
  onToggleAnalyzeWhileTyping: (enabled: boolean) => void;
  onCloseFlyout: () => void;
  onNewFile: () => void;
  onOpenFile: () => void;
  onFolder: () => void;
  onSave: () => void;
  onSwitchDoc: (id: string) => void;
  onCloseDoc: (id?: string) => void;
  onSample: (sample: SampleItem) => void;
}

export const AppActivityStrip: React.FC<AppActivityStripProps> = ({
  flyout,
  onToggleFlyout,
  flyoutRef,
  openDocs,
  activeDocId,
  samples,
  language,
  engine,
  themeMode,
  themeResolved,
  onThemeChange,
  analyzeWhileTyping,
  onToggleAnalyzeWhileTyping,
  onCloseFlyout,
  onNewFile,
  onOpenFile,
  onFolder,
  onSave,
  onSwitchDoc,
  onCloseDoc,
  onSample,
}) => {
  return (
    <>
      <aside data-qa="strip" className="ui5-strip" aria-label="Panels">
        <button
          aria-label="Files"
          title="Files"
          aria-pressed={flyout === 'files'}
          onClick={(event) => onToggleFlyout('files', event.currentTarget)}
        >
          <Files size={17} strokeWidth={1.5} />
        </button>
        <button
          aria-label="Samples"
          title="Samples"
          aria-pressed={flyout === 'samples'}
          onClick={(event) => onToggleFlyout('samples', event.currentTarget)}
        >
          <FlaskConical size={17} strokeWidth={1.5} />
        </button>
        <button
          aria-label="Help"
          title="Help"
          aria-pressed={flyout === 'help'}
          onClick={(event) => onToggleFlyout('help', event.currentTarget)}
        >
          <CircleHelp size={17} strokeWidth={1.5} />
        </button>
      </aside>

      {flyout && (
        <div ref={flyoutRef}>
          <FlyoutPanel
            mode={flyout}
            files={openDocs}
            activeId={activeDocId}
            samples={samples}
            language={language}
            engine={engine}
            themeMode={themeMode}
            themeResolved={themeResolved}
            onThemeChange={onThemeChange}
            analyzeWhileTyping={analyzeWhileTyping}
            onToggleAnalyzeWhileTyping={onToggleAnalyzeWhileTyping}
            onClose={onCloseFlyout}
            onNew={onNewFile}
            onOpen={onOpenFile}
            onFolder={onFolder}
            onSave={onSave}
            onSwitch={onSwitchDoc}
            onCloseFile={onCloseDoc}
            onSample={onSample}
          />
        </div>
      )}
    </>
  );
};
