import React from 'react';
import { X } from 'lucide-react';
import type { SampleItem } from '../api/client';
import type { ResolvedTheme, ThemeMode } from '../theme/theme';
import { FlyoutFiles } from './FlyoutFiles';
import { FlyoutSamples } from './FlyoutSamples';
import { FlyoutHelp } from './FlyoutHelp';

export type FlyoutMode = 'files' | 'samples' | 'help';
export type FlyoutFile = {
  id: string;
  name: string;
  dirty: boolean;
  language: string;
  folderPath?: string;
};

type Props = {
  mode: FlyoutMode;
  files: FlyoutFile[];
  activeId: string | null;
  samples: SampleItem[];
  language: string;
  engine?: { parser?: string; ml_mode?: string; ml_model_id?: string; ml_reason?: string } | null;
  onClose: () => void;
  onNew: () => void;
  onOpen: () => void;
  onFolder: () => void;
  onSave: () => void;
  onSwitch: (id: string) => void;
  onCloseFile: (id: string) => void;
  onSample: (sample: SampleItem) => void;
  themeMode?: ThemeMode;
  themeResolved?: ResolvedTheme;
  onThemeChange?: (mode: ThemeMode) => void;
  analyzeWhileTyping?: boolean;
  onToggleAnalyzeWhileTyping?: (enabled: boolean) => void;
};

export const FlyoutPanel: React.FC<Props> = ({
  mode,
  files,
  activeId,
  samples,
  language,
  engine,
  onClose,
  onNew,
  onOpen,
  onFolder,
  onSave,
  onSwitch,
  onCloseFile,
  onSample,
  themeMode = 'dark',
  onThemeChange = () => {},
  analyzeWhileTyping = false,
  onToggleAnalyzeWhileTyping,
}) => {
  return (
    <section className="ui6-flyout" role="dialog" aria-label={`${mode} panel`}>
      <header>
        <strong>{mode === 'files' ? 'Files' : mode === 'samples' ? 'Samples' : 'Help'}</strong>
        <button aria-label="Close panel" onClick={onClose}>
          <X size={15} />
        </button>
      </header>

      {mode === 'files' && (
        <FlyoutFiles
          files={files}
          activeId={activeId}
          onNew={onNew}
          onOpen={onOpen}
          onFolder={onFolder}
          onSave={onSave}
          onSwitch={onSwitch}
          onCloseFile={onCloseFile}
        />
      )}

      {mode === 'samples' && (
        <FlyoutSamples samples={samples} language={language} onSample={onSample} />
      )}

      {mode === 'help' && (
        <FlyoutHelp
          themeMode={themeMode}
          onThemeChange={onThemeChange}
          analyzeWhileTyping={analyzeWhileTyping}
          onToggleAnalyzeWhileTyping={onToggleAnalyzeWhileTyping}
          engine={engine}
        />
      )}
    </section>
  );
};
