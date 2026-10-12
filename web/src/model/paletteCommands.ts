import { PaletteCommand } from '../components/CommandPalette';
import { SampleItem, LanguageInfo } from '../api/client';
import { ThemeMode } from '../theme/theme';

interface BuildPaletteCommandsOptions {
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
  createNewFile: () => void;
  onOpenFileClick: () => void;
  onFolderClick: () => void;
  handleDownload: () => void;
  closeCurrentFile: () => void;
  runAnalysis: () => void;
  handleFixAll: () => void;
  safeFixCount: number;
  handleNextProblem: () => void;
  handlePrevProblem: () => void;
  onSetTab: (tab: any) => void;
  setTokenMap: React.Dispatch<React.SetStateAction<'off' | 'security' | 'full'>>;
  onToggleSidebar: () => void;
  samples: SampleItem[];
  handleSelectSample: (sample: SampleItem) => void;
  languages: LanguageInfo[];
  onSetLanguage: (lang: string) => void;
  onOpenShortcuts: () => void;
  onExplainToken: () => void;
  onProposeFix: () => void;
  onOpenSafetyLab: () => void;
  onExportReport: () => void;
  onOpenAst: () => void;
  onShowSecurity: () => void;
  onBuildWithAI: () => void;
  onUndoFix: () => void;
}

export function buildPaletteCommands(opts: BuildPaletteCommandsOptions): PaletteCommand[] {
  return [
    { label: 'Theme: Dark', run: () => opts.setThemeMode('dark') },
    { label: 'Theme: Light', run: () => opts.setThemeMode('light') },
    { label: 'Theme: System', run: () => opts.setThemeMode('system') },
    { label: 'Toggle theme', run: opts.toggleTheme },
    { label: 'New File', run: opts.createNewFile },
    { label: 'Open File', run: opts.onOpenFileClick },
    { label: 'Open Folder', run: opts.onFolderClick },
    { label: 'Save', run: opts.handleDownload },
    { label: 'Close File', run: opts.closeCurrentFile },
    {
      label: 'Analyze',
      run: opts.runAnalysis,
    },
    {
      label: `Fix All (${opts.safeFixCount})`,
      run: opts.handleFixAll,
    },
    { label: 'Next Problem', run: opts.handleNextProblem },
    { label: 'Previous Problem', run: opts.handlePrevProblem },
    {
      label: 'Show Token Security',
      run: () => opts.onSetTab('tokens'),
    },
    {
      label: 'Toggle Token Map',
      run: () =>
        opts.setTokenMap((mode) =>
          mode === 'off' ? 'security' : mode === 'security' ? 'full' : 'off'
        ),
    },
    {
      label: 'Show Summary',
      run: () => opts.onSetTab('summary'),
    },
    {
      label: 'Show ML Insights',
      run: () => opts.onSetTab('ml'),
    },
    { label: 'Toggle Sidebar', run: opts.onToggleSidebar },
    ...opts.samples.slice(0, 20).map((sample) => ({
      label: `Open Sample: ${sample.title}`,
      run: () => opts.handleSelectSample(sample),
      keywords: sample.language,
    })),
    ...opts.languages.map((language) => ({
      label: `Change Language: ${language.display_name}`,
      run: () => opts.onSetLanguage(language.id),
    })),
    { label: 'Keyboard Shortcuts', run: opts.onOpenShortcuts },
    { label: 'Explain selected token', run: opts.onExplainToken, keywords: 'Ctrl+Shift+E' },
    { label: 'Propose a fix', run: opts.onProposeFix, keywords: 'Ctrl+Shift+F' },
    { label: 'Open Safety Lab', run: opts.onOpenSafetyLab },
    { label: 'Export report', run: opts.onExportReport },
    { label: 'Open AST', run: opts.onOpenAst },
    { label: 'Show Security', run: opts.onShowSecurity },
    { label: 'Build with AI', run: opts.onBuildWithAI },
    { label: 'Undo fix', run: opts.onUndoFix, keywords: 'Ctrl+Z' },
  ];
}
