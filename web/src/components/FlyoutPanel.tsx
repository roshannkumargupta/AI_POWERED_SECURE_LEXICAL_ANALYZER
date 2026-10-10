import React, { useMemo, useState } from 'react';
import { FileCode2, FolderOpen, X, Download } from 'lucide-react';
import type { SampleItem } from '../api/client';
import { LEVELS, levelOf, searchSamples } from '../utils/sampleDemo';
import { DEMO_PATH } from '../utils/sampleDemo';
import { computeUiScale } from '../utils/uiScale';
import type { ResolvedTheme, ThemeMode } from '../theme/theme';

export type FlyoutMode = 'files' | 'samples' | 'help';
export type FlyoutFile = { id: string; name: string; dirty: boolean; language: string; folderPath?: string };
type Props = {
  mode: FlyoutMode; files: FlyoutFile[]; activeId: string | null; samples: SampleItem[]; language: string;
  engine?: { parser?: string; ml_mode?: string; ml_model_id?: string; ml_reason?: string } | null; onClose: () => void; onNew: () => void;
  onOpen: () => void; onFolder: () => void; onSave: () => void; onSwitch: (id: string) => void;
  onCloseFile: (id: string) => void; onSample: (sample: SampleItem) => void;
  themeMode?: ThemeMode; themeResolved?: ResolvedTheme; onThemeChange?: (mode: ThemeMode) => void;
  analyzeWhileTyping?: boolean; onToggleAnalyzeWhileTyping?: (enabled: boolean) => void;
};

const languageName = (language: string) => language === 'cpp' ? 'C/C++' : language === 'javascript' ? 'JavaScript' : `${language[0]?.toUpperCase() || ''}${language.slice(1)}`;

export const FlyoutPanel: React.FC<Props> = ({ mode, files, activeId, samples, language, engine, onClose, onNew, onOpen, onFolder, onSave, onSwitch, onCloseFile, onSample, themeMode = 'dark', themeResolved: _themeResolved = 'dark', onThemeChange = () => {}, analyzeWhileTyping = false, onToggleAnalyzeWhileTyping }) => {
  const [query, setQuery] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});
  const [interfaceSize, setInterfaceSize] = useState(() => {
    try { return localStorage.getItem('securelex-interface-size') || '1'; } catch { return '1'; }
  });
  const changeInterfaceSize = (value: string) => {
    setInterfaceSize(value);
    try { localStorage.setItem('securelex-interface-size', value); } catch { /* storage may be blocked */ }
    const scale = computeUiScale(window.innerWidth, window.innerHeight, Number(value) as 0.85 | 1 | 1.15);
    document.documentElement.style.setProperty('--ui-scale', String(scale));
    document.documentElement.style.setProperty('--ui-frame-size', `${100 / scale}%`);
  };
  const filtered = useMemo(() => searchSamples(samples, query), [samples, query]);
  const languages = ['python', 'java', 'javascript', 'cpp'];
  const visibleLanguages = showAll || language === 'auto' ? languages : [language];
  return <section className="ui6-flyout" role="dialog" aria-label={`${mode} panel`}>
    <header><strong>{mode === 'files' ? 'Files' : mode === 'samples' ? 'Samples' : 'Help'}</strong><button aria-label="Close panel" onClick={onClose}><X size={15}/></button></header>
    {mode === 'files' && <>
      <div className="ui6-flyout-actions"><button onClick={onNew}><FileCode2 size={14}/>New file <kbd>Ctrl+N</kbd></button><button onClick={onOpen}><FileCode2 size={14}/>Open file <kbd>Ctrl+O</kbd></button><button onClick={onFolder}><FolderOpen size={14}/>Open folder</button></div>
      {files.some((file) => file.folderPath) && <><div className="ui6-flyout-section">WORKSPACE <span>{files.filter((file)=>file.folderPath).length}</span></div><div role="tree" className="ui6-workspace-tree">{files.filter((file)=>file.folderPath).map((file)=><button role="treeitem" aria-selected={file.id===activeId} key={file.id} onClick={()=>onSwitch(file.id)} title={file.folderPath}>{file.folderPath}</button>)}</div></>}
      <div className="ui6-flyout-section">OPEN FILES <span>{files.length}</span></div>
      <div className="ui6-open-files">{files.map((file) => <div key={file.id} className={`ui6-file-row ${file.id === activeId ? 'active' : ''}`}>
        <button className="ui6-file-name" onClick={() => onSwitch(file.id)}><span aria-hidden="true">{file.language === 'auto' ? '◈' : '⌘'}</span><span>{file.name}</span>{file.dirty && <i aria-label="Unsaved changes" title="Unsaved changes"/>}</button>
        <button className="ui6-file-close" aria-label={`Close ${file.name}`} onClick={() => onCloseFile(file.id)}><X size={13}/></button>
      </div>)}</div>
      <div className="ui6-flyout-bottom"><button onClick={onSave}><Download size={14}/>Save / Download <kbd>Ctrl+S</kbd></button></div>
    </>}
    {mode === 'samples' && <>
      <input className="ui6-search" aria-label="Search samples" placeholder="Search samples" value={query} onChange={(event) => setQuery(event.target.value)}/>
      <button className="ui6-show-languages" onClick={() => setShowAll((value) => !value)}>{showAll ? 'Show active language' : 'Show all languages'}</button>
      <div className="ui6-samples-list">{visibleLanguages.map((lang) => {
        const groupRows = filtered.filter((sample) => sample.language === lang);
        const targetDemos = lang === 'python' ? groupRows.filter((sample) => /Target Demo/i.test(sample.title)) : [];
        const ordinary = groupRows.filter((sample) => !targetDemos.includes(sample));
        const expanded = openGroups[lang] ?? language !== 'auto';
        return <div key={lang}>
          <button className="ui6-group" aria-expanded={expanded} onClick={() => setOpenGroups((current) => ({ ...current, [lang]: !expanded }))}>{languageName(lang)}<span>{groupRows.length}</span></button>
          {expanded && <>
            {targetDemos.map((sample) => <button key={sample.id} className="ui6-sample" onClick={() => onSample(sample)} title={sample.description}>{sample.title}</button>)}
            {LEVELS.map((level) => {
              const levelSamples = ordinary.filter((sample) => levelOf(sample) === level);
              if (!levelSamples.length) return null;
              const key = `${lang}:${level}`; const levelOpen = openGroups[key] ?? false;
              const label = level === 'safe' ? 'Safe code' : level === 'lexer' ? 'Lexer showcase' : level[0].toUpperCase()+level.slice(1);
              return <div key={key}><button className="ui6-group level" aria-expanded={levelOpen} onClick={() => setOpenGroups((current) => ({...current,[key]:!levelOpen}))}>{label}<span>{levelSamples.length}</span></button>{levelOpen && levelSamples.map((sample) => <button key={sample.id} className="ui6-sample" onClick={() => onSample(sample)} title={sample.description}>{sample.title}</button>)}</div>;
            })}
          </>}
        </div>;
      })}</div>
      {samples.find((sample) => sample.notes?.length || sample.demo_order) && <details className="ui6-demo-notes"><summary>Demo path and notes</summary><ol>{DEMO_PATH.map((id) => samples.find((sample) => sample.id === id)).filter((sample): sample is SampleItem => Boolean(sample)).map((sample) => <li key={sample.id}><button onClick={() => onSample(sample)}>{sample.title}</button>{sample.notes?.[0] && <small> — {sample.notes[0]}</small>}</li>)}</ol></details>}
    </>}
    {mode === 'help' && <div className="ui6-help">
      <div className="ui6-flyout-section"><label htmlFor="securelex-interface-size">INTERFACE SIZE</label></div>
      <div className="ui6-shortcut"><span>Scale the workspace</span><select id="securelex-interface-size" aria-label="Interface size" value={interfaceSize} onChange={(event) => changeInterfaceSize(event.target.value)}><option value="0.85">Compact</option><option value="1">Reference</option><option value="1.15">Large</option></select></div>
      <div className="ui6-flyout-section">APPEARANCE</div>
      <div className="ui6-theme-options" role="radiogroup" aria-label="Appearance">
        {(['dark', 'light', 'system'] as const).map((choice) => <button key={choice} type="button" role="radio" aria-checked={themeMode === choice} className="ui6-theme-option" onClick={() => onThemeChange(choice)}>{choice[0].toUpperCase() + choice.slice(1)}</button>)}
      </div>
      <div className="ui6-flyout-section">ANALYSIS SETTINGS</div>
      <div className="ui6-shortcut" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Analyze while typing</span>
        <input
          type="checkbox"
          id="setting-analyze-typing"
          aria-label="Analyze while typing"
          checked={Boolean(analyzeWhileTyping)}
          onChange={(e) => onToggleAnalyzeWhileTyping?.(e.target.checked)}
          style={{ cursor: 'pointer', width: 16, height: 16 }}
        />
      </div>
      <div className="ui6-flyout-section">KEYBOARD SHORTCUTS</div>
      {[['Ctrl+Enter','Analyze'],['Ctrl+.','Quick fix'],['F8 / Shift+F8','Next / previous problem'],['Ctrl+B','Toggle last panel'],['Ctrl+N','New file'],['Ctrl+O','Open file'],['Ctrl+S','Save / download'],['Ctrl+W','Close file'],['Ctrl+Shift+P','Command palette']].map(([key,label]) => <div className="ui6-shortcut" key={key}><span>{label}</span><kbd>{key}</kbd></div>)}
      <div className="ui6-flyout-section">TIPS</div><p>Samples open as editable files.</p><p>Click a token row or code range to inspect its evidence.</p><p>Only verified safe fixes can be applied automatically.</p>
      <div className="ui6-flyout-section">ENGINE</div><p>Parser: Python ast; other languages lexer-only</p><p>ML status: {engine?.ml_mode === 'on' ? `on — model ${engine.ml_model_id || 'id not reported'}` : `off — reason: ${engine?.ml_reason || 'not provided by the API'}`}</p>
    </div>}
  </section>;
};
