import React from 'react';
import type { IDEDocument } from '../state/store';

interface EditorTabsProps {
  documents: IDEDocument[];
  activeDocId: string | null;
  onSelectDoc: (id: string) => void;
  onCloseDoc: (id: string) => void;
}

export const EditorTabs: React.FC<EditorTabsProps> = ({
  documents,
  activeDocId,
  onSelectDoc,
  onCloseDoc,
}) => {
  return (
    <div className="flex items-center gap-1 min-w-0 overflow-x-auto">
      {documents.map((doc) => {
        const isActive = doc.id === activeDocId;
        const displayName = doc.name.replace(/^src\//, '');
        return (
          <div
            key={doc.id}
            onClick={() => onSelectDoc(doc.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-t-md text-[11px] font-medium cursor-pointer transition-all shadow-xs ${
              isActive
                ? 'bg-surface-editor border-t-2 border-t-primary border-x border-border-subtle text-text-primary'
                : 'bg-surface-deepest/60 border-t-2 border-transparent text-text-secondary hover:text-text-primary hover:bg-surface-hover/50'
            }`}
            id={isActive ? 'editorActiveTab' : undefined}
          >
            <span
              className={`material-symbols-outlined text-[14px] ${isActive ? 'text-primary' : 'text-text-muted'}`}
            >
              description
            </span>
            <span className={`font-mono ${isActive ? 'font-semibold' : ''}`}>{displayName}</span>
            {doc.dirty && (
              <span
                className="w-1.5 h-1.5 rounded-full bg-status-warning"
                title="Unsaved changes / analysis required"
              />
            )}
            <button
              type="button"
              className="hover:text-status-error p-0.5 rounded text-text-muted hover:bg-surface-hover ml-1 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                onCloseDoc(doc.id);
              }}
              title="Close tab"
            >
              <span className="material-symbols-outlined text-[12px]">close</span>
            </button>
          </div>
        );
      })}
    </div>
  );
};

