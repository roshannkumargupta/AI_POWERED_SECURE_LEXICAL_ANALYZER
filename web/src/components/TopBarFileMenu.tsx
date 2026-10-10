import React from 'react';
import { ChevronDown } from 'lucide-react';
import { secondaryButtonStyle, dropdownMenuStyle, dropdownItemStyle } from './topBarStyles';

export type OpenFile = { id: string; name: string; dirty: boolean };

interface TopBarFileMenuProps {
  onNewFile: () => void;
  onOpenFile: () => void;
  onCloseFile: () => void;
  filename: string;
  files: OpenFile[];
  activeFileId: string | null;
  onSwitchFile?: (id: string) => void;
  onCloseFileById?: (id: string) => void;
}

export const TopBarFileMenu: React.FC<TopBarFileMenuProps> = ({
  onNewFile,
  onOpenFile,
  onCloseFile,
  filename,
  files,
  activeFileId,
  onSwitchFile,
  onCloseFileById,
}) => {
  const [isFileMenuOpen, setIsFileMenuOpen] = React.useState(false);
  const [isFileListOpen, setIsFileListOpen] = React.useState(false);

  return (
    <>
      <div style={{ position: 'relative' }}>
        <button
          style={secondaryButtonStyle}
          onClick={() => setIsFileMenuOpen((open) => !open)}
          aria-label="File menu"
        >
          File
        </button>
        {isFileMenuOpen && (
          <div style={dropdownMenuStyle}>
            <button
              style={dropdownItemStyle}
              onClick={() => {
                onNewFile();
                setIsFileMenuOpen(false);
              }}
            >
              New File <small>Ctrl+N</small>
            </button>
            <button
              style={dropdownItemStyle}
              onClick={() => {
                onOpenFile();
                setIsFileMenuOpen(false);
              }}
            >
              Open File... <small>Ctrl+O</small>
            </button>
            <button
              style={dropdownItemStyle}
              onClick={() => {
                onCloseFile();
                setIsFileMenuOpen(false);
              }}
            >
              Close File <small>Ctrl+W</small>
            </button>
          </div>
        )}
      </div>

      <div style={{ position: 'relative' }}>
        <button
          aria-label="Open file list"
          aria-expanded={isFileListOpen}
          onClick={() => setIsFileListOpen((open) => !open)}
          title={filename || 'No file open'}
          style={{
            color: 'var(--text-primary)',
            fontSize: 12,
            maxWidth: 220,
            height: 26,
            display: 'inline-flex',
            alignItems: 'center',
            padding: '0 9px',
            border: '1px solid var(--border)',
            borderRadius: 8,
            background: 'var(--surface-2)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {filename || 'No file'} <ChevronDown size={12} />
        </button>
        {isFileListOpen && (
          <div style={dropdownMenuStyle} role="menu" aria-label="Open files">
            {files.map((file) => (
              <div key={file.id} style={{ display: 'flex', alignItems: 'center' }}>
                <button
                  role="menuitem"
                  aria-current={file.id === activeFileId ? 'true' : undefined}
                  style={{ ...dropdownItemStyle, flex: 1 }}
                  onClick={() => {
                    onSwitchFile?.(file.id);
                    setIsFileListOpen(false);
                  }}
                >
                  {file.name}
                  {file.dirty ? ' •' : ''}
                </button>
                <button
                  aria-label={`Close ${file.name}`}
                  onClick={() => onCloseFileById?.(file.id)}
                >
                  ×
                </button>
              </div>
            ))}
            <button
              role="menuitem"
              style={dropdownItemStyle}
              onClick={() => {
                onNewFile();
                setIsFileListOpen(false);
              }}
            >
              New
            </button>
            <button
              role="menuitem"
              style={dropdownItemStyle}
              onClick={() => {
                onOpenFile();
                setIsFileListOpen(false);
              }}
            >
              Open
            </button>
          </div>
        )}
      </div>
    </>
  );
};
