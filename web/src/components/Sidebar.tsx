import React, { useRef } from 'react';
import {
  FolderOpen,
  FileCode,
  AlertOctagon,
  Sparkles,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { SampleItem } from '../api/client';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  samples: SampleItem[];
  selectedSampleId: string | null;
  onSelectSample: (sample: SampleItem) => void;
  onOpenFile: (filename: string, content: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  samples,
  selectedSampleId,
  onSelectSample,
  onOpenFile,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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
          accept=".py,.java,.js,.jsx,.ts,.tsx,.cpp,.cc,.h"
        />
        <button
          style={openFileButtonStyle}
          onClick={() => fileInputRef.current?.click()}
        >
          <FolderOpen size={14} />
          <span>Open Local File...</span>
        </button>
      </div>

      {/* Samples List */}
      <div style={samplesSectionStyle}>
        <div style={sectionHeaderStyle}>
          <span>TEST FIXTURES & SAMPLES</span>
          <span style={badgeCountStyle}>{samples.length}</span>
        </div>

        <div style={samplesListStyle}>
          {samples.map((sample) => {
            const isSelected = sample.id === selectedSampleId;
            let icon = <FileCode size={14} color="var(--accent)" />;
            if (sample.category === 'vulnerable') {
              icon = <AlertOctagon size={14} color="var(--critical)" />;
            } else if (sample.category === 'adversarial') {
              icon = <Sparkles size={14} color="var(--high)" />;
            } else if (sample.category === 'safe') {
              icon = <CheckCircle2 size={14} color="var(--success)" />;
            }

            return (
              <button
                key={sample.id}
                style={{
                  ...sampleItemStyle,
                  backgroundColor: isSelected ? 'var(--panel-3)' : 'transparent',
                  borderLeft: isSelected ? '2px solid var(--accent)' : '2px solid transparent',
                }}
                onClick={() => onSelectSample(sample)}
                title={sample.description}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <div style={{ marginTop: '2px' }}>{icon}</div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <span style={sampleTitleStyle}>{sample.title}</span>
                    <span style={sampleFilenameStyle}>{sample.filename}</span>
                  </div>
                </div>
              </button>
            );
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

const sampleFilenameStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  fontFamily: 'var(--font-code)',
  marginTop: '2px',
};
