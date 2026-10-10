import React from 'react';
import { FileCode2, FolderOpen, X, Download } from 'lucide-react';
import type { FlyoutFile } from './FlyoutPanel';

interface FlyoutFilesProps {
  files: FlyoutFile[];
  activeId: string | null;
  onNew: () => void;
  onOpen: () => void;
  onFolder: () => void;
  onSave: () => void;
  onSwitch: (id: string) => void;
  onCloseFile: (id: string) => void;
}

export const FlyoutFiles: React.FC<FlyoutFilesProps> = ({
  files,
  activeId,
  onNew,
  onOpen,
  onFolder,
  onSave,
  onSwitch,
  onCloseFile,
}) => {
  return (
    <>
      <div className="ui6-flyout-actions">
        <button onClick={onNew}>
          <FileCode2 size={14} />
          New file <kbd>Ctrl+N</kbd>
        </button>
        <button onClick={onOpen}>
          <FileCode2 size={14} />
          Open file <kbd>Ctrl+O</kbd>
        </button>
        <button onClick={onFolder}>
          <FolderOpen size={14} />
          Open folder
        </button>
      </div>
      {files.some((file) => file.folderPath) && (
        <>
          <div className="ui6-flyout-section">
            WORKSPACE <span>{files.filter((file) => file.folderPath).length}</span>
          </div>
          <div role="tree" className="ui6-workspace-tree">
            {files
              .filter((file) => file.folderPath)
              .map((file) => (
                <button
                  role="treeitem"
                  aria-selected={file.id === activeId}
                  key={file.id}
                  onClick={() => onSwitch(file.id)}
                  title={file.folderPath}
                >
                  {file.folderPath}
                </button>
              ))}
          </div>
        </>
      )}
      <div className="ui6-flyout-section">
        OPEN FILES <span>{files.length}</span>
      </div>
      <div className="ui6-open-files">
        {files.map((file) => (
          <div key={file.id} className={`ui6-file-row ${file.id === activeId ? 'active' : ''}`}>
            <button className="ui6-file-name" onClick={() => onSwitch(file.id)}>
              <span aria-hidden="true">{file.language === 'auto' ? '◈' : '⌘'}</span>
              <span>{file.name}</span>
              {file.dirty && <i aria-label="Unsaved changes" title="Unsaved changes" />}
            </button>
            <button
              className="ui6-file-close"
              aria-label={`Close ${file.name}`}
              onClick={() => onCloseFile(file.id)}
            >
              <X size={13} />
            </button>
          </div>
        ))}
      </div>
      <div className="ui6-flyout-bottom">
        <button onClick={onSave}>
          <Download size={14} />
          Save / Download <kbd>Ctrl+S</kbd>
        </button>
      </div>
    </>
  );
};
