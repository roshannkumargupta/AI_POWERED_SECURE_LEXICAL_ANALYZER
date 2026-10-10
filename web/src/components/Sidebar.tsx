import React, { useRef } from 'react';
import { useState } from 'react';
import { FolderOpen, FileCode, ChevronLeft, ChevronRight } from 'lucide-react';
import { SampleItem } from '../api/client';
import { DEMO_PATH, LEVELS, searchSamples, levelOf } from '../utils/sampleDemo';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  samples: SampleItem[];
  selectedSampleId: string | null;
  onSelectSample: (sample: SampleItem) => void;
  onOpenFile: (filename: string, content: string) => void;
  onNewFile: () => void;
  onChooseFile: () => void;
  language: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  samples,
  selectedSampleId,
  onSelectSample,
  onOpenFile,
  onNewFile,
  onChooseFile,
  language,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [query, setQuery] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [demoOpen, setDemoOpen] = useState(false);
  const visible = searchSamples(samples, query);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content !== undefined) {
        onOpenFile(file.name, content);
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  if (isCollapsed) {
    return (
      <div style={collapsedContainerStyle}>
        <button
          style={expandBtnStyle}
          onClick={onToggleCollapse}
          title="Expand Samples Sidebar"
          aria-label="Expand Samples Sidebar"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    );
  }

  return (
    <aside style={containerStyle}>
      {/* Sidebar Header */}
      <div style={headerStyle}>
        <span style={titleStyle}>Explorer & Presets</span>
        <button
          style={collapseBtnStyle}
          onClick={onToggleCollapse}
          title="Collapse Sidebar"
          aria-label="Collapse Sidebar"
        >
          <ChevronLeft size={16} />
        </button>
      </div>

      {/* Open File Button */}
      <div style={openFileBoxStyle}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }}
          accept=".py,.java,.js,.jsx,.ts,.tsx,.cpp,.cc,.c,.h,.hpp"
        />
        <div style={{ display: 'flex', gap: 6 }}>
          <button style={openFileButtonStyle} onClick={onNewFile}><FileCode size={14} /><span>New file</span></button>
          <button style={openFileButtonStyle} onClick={onChooseFile}><FolderOpen size={14} /><span>Open file</span></button>
        </div>
      </div>

      {/* Samples List */}
      <div style={samplesSectionStyle}>
        <div style={sectionHeaderStyle}>
          <span>SAMPLES</span>
          <span style={badgeCountStyle}>{samples.filter((s) => showAll || language === 'auto' || s.language === language).length}</span>
        </div>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search samples" aria-label="Search samples" style={{ margin: '4px 10px 8px', padding: '6px 8px', background: 'var(--bg)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }} />
        <button onClick={() => setShowAll((value) => !value)} style={{ margin: '0 10px 6px', color: 'var(--accent)', background: 'transparent', border: 0, textAlign: 'left', cursor: 'pointer' }}>{showAll ? 'Show active language' : 'Show all languages'}</button>

        <div style={samplesListStyle}>
          <button aria-expanded={demoOpen} onClick={() => setDemoOpen((open) => !open)} style={groupHeaderStyle}>DEMO PATH <span style={badgeCountStyle}>13</span></button>
          {demoOpen && DEMO_PATH.map((id, index) => { const sample = samples.find((item) => item.id === id); return sample ? <button key={id} style={sampleItemStyle} onClick={() => onSelectSample(sample)} title={sample.summary || sample.description}>{index + 1}. {sample.title}</button> : null; })}
          {(showAll || language === 'auto' ? ['python', 'java', 'javascript', 'cpp'] : [language]).map((group) => {
            const groupSamples = visible.filter((s) => s.language === group);
            const label = group === 'cpp' ? 'C/C++' : group === 'javascript' ? 'JavaScript' : group[0].toUpperCase() + group.slice(1);
            const expanded = expandedGroups[group] ?? showAll;
            return <React.Fragment key={group}>
            {(language === 'auto' || showAll) && <button aria-expanded={expanded} onKeyDown={(event) => { if (event.key === 'ArrowRight') setExpandedGroups((current) => ({ ...current, [group]: true })); if (event.key === 'ArrowLeft') setExpandedGroups((current) => ({ ...current, [group]: false })); }} onClick={() => setExpandedGroups((current) => ({ ...current, [group]: !current[group] }))} style={groupHeaderStyle}>{label}<span style={badgeCountStyle}>{groupSamples.length}</span></button>}
            {(expanded || (language !== 'auto' && !showAll && group === language)) && LEVELS.map((level) => {
              const levelSamples = groupSamples.filter((sample) => levelOf(sample) === level);
              if (!levelSamples.length) return null;
              const key = `${group}:${level}`;
              const open = expandedGroups[key] ?? level === 'basic';
              const levelTitle = level === 'safe' ? 'Safe code' : level === 'unicode' ? 'Unicode' : level === 'lexer' ? 'Lexer showcase' : level[0].toUpperCase() + level.slice(1);
              return <React.Fragment key={key}><button aria-expanded={open} onKeyDown={(event) => { if (event.key === 'ArrowRight') setExpandedGroups((current) => ({ ...current, [key]: true })); if (event.key === 'ArrowLeft') setExpandedGroups((current) => ({ ...current, [key]: false })); }} onClick={() => setExpandedGroups((current) => ({ ...current, [key]: !open }))} style={groupHeaderStyle}>{levelTitle}<span style={badgeCountStyle}>{levelSamples.length}</span></button>{open && levelSamples.map((sample) => {
            const isSelected = sample.id === selectedSampleId;
            const chip = level === 'safe' ? 'Safe' : level === 'lexer' ? 'Lexer' : level === 'unicode' ? 'Unicode' : 'Vulnerable';

            return (
              <button
                key={sample.id}
                data-sample-row="true"
                style={{
                  ...sampleItemStyle,
                  backgroundColor: isSelected ? 'var(--panel-3)' : 'transparent',
                  borderLeft: isSelected ? '2px solid var(--accent)' : '2px solid transparent',
                }}
                onClick={() => onSelectSample(sample)}
                onKeyDown={(event) => { if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); const rows = Array.from(document.querySelectorAll<HTMLButtonElement>('[data-sample-row="true"]')); const index = rows.indexOf(event.currentTarget); rows[index + (event.key === 'ArrowDown' ? 1 : -1)]?.focus(); } }}
                title={sample.description}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <span style={sampleTitleStyle}>{sample.title}</span>
                    <span style={sampleLabelStyle}>{chip}</span>
                  </div>
                </div>
              </button>
            );
          })}</React.Fragment>;
            })}
            </React.Fragment>;
          })}
        </div>
      </div>
    </aside>
  );
};

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  backgroundColor: 'var(--panel)',
  display: 'flex',
  flexDirection: 'column',
  borderRight: '1px solid var(--border)',
  overflow: 'hidden',
};

const collapsedContainerStyle: React.CSSProperties = {
  width: '32px',
  height: '100%',
  backgroundColor: 'var(--panel)',
  borderRight: '1px solid var(--border)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  paddingTop: '8px',
};

const expandBtnStyle: React.CSSProperties = {
  padding: '6px',
  color: 'var(--muted)',
  borderRadius: 'var(--radius-sm)',
};

const headerStyle: React.CSSProperties = {
  height: '36px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 12px',
  borderBottom: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
};

const titleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

const collapseBtnStyle: React.CSSProperties = {
  padding: '4px',
  color: 'var(--muted)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const openFileBoxStyle: React.CSSProperties = {
  padding: '10px 12px',
  borderBottom: '1px solid var(--border)',
};

const openFileButtonStyle: React.CSSProperties = {
  width: '100%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '8px',
  padding: '6px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
};

const samplesSectionStyle: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflowY: 'auto',
  padding: '10px 0',
};

const sectionHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 12px 6px 12px',
  fontSize: '10px',
  fontWeight: 700,
  color: 'var(--muted)',
  letterSpacing: '0.4px',
};

const badgeCountStyle: React.CSSProperties = {
  fontSize: '9px',
  fontWeight: 600,
  backgroundColor: 'var(--panel-2)',
  padding: '1px 5px',
  borderRadius: 'var(--radius-full)',
  color: 'var(--text-secondary)',
};

const samplesListStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
};

const groupHeaderStyle: React.CSSProperties = {
  display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%',
  padding: '6px 12px', color: 'var(--text-secondary)', background: 'transparent', border: 0,
  textAlign: 'left', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer',
};

const sampleItemStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  padding: '8px 12px',
  textAlign: 'left',
  cursor: 'pointer',
  transition: 'background-color var(--transition-fast)',
  borderBottom: '1px solid var(--border-subtle)',
};

const sampleTitleStyle: React.CSSProperties = {
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text)',
  lineHeight: 1.3,
};

const sampleLabelStyle: React.CSSProperties = {
  marginTop: 4, padding: '1px 5px', border: '1px solid var(--border)', borderRadius: 'var(--radius-full)',
  color: 'var(--muted)', fontSize: 9, lineHeight: '14px',
};
