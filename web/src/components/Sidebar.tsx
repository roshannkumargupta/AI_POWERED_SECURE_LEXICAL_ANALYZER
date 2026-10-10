import React, { useRef } from 'react';
import { FolderOpen, FileCode, ChevronLeft, ChevronRight } from 'lucide-react';
import { SampleItem } from '../api/client';
import {
  containerStyle,
  collapsedContainerStyle,
  expandBtnStyle,
  headerStyle,
  titleStyle,
  collapseBtnStyle,
  openFileBoxStyle,
  openFileButtonStyle,
} from './sidebarStyles';
import { SidebarSampleList } from './SidebarSampleList';

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
          <button style={openFileButtonStyle} onClick={onNewFile}>
            <FileCode size={14} />
            <span>New file</span>
          </button>
          <button style={openFileButtonStyle} onClick={onChooseFile}>
            <FolderOpen size={14} />
            <span>Open file</span>
          </button>
        </div>
      </div>

      {/* Samples List */}
      <SidebarSampleList
        samples={samples}
        selectedSampleId={selectedSampleId}
        onSelectSample={onSelectSample}
        language={language}
      />
    </aside>
  );
};
