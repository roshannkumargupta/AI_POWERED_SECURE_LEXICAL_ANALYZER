import React, { useState, useEffect, useRef } from 'react';

export interface CommandItem {
  id: string;
  title: string;
  category: string;
  shortcut?: string;
  icon?: string;
  action: () => void;
}

interface CommandPaletteModalProps {
  isOpen: boolean;
  onClose: () => void;
  commands: CommandItem[];
}

export const CommandPaletteModal: React.FC<CommandPaletteModalProps> = ({
  isOpen,
  onClose,
  commands,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const filtered = commands.filter((cmd) => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      cmd.title.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q) ||
      cmd.id.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1 < filtered.length ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 >= 0 ? prev - 1 : filtered.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
        onClose();
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  useEffect(() => {
    if (listRef.current) {
      const activeEl = listRef.current.querySelector('[data-selected="true"]');
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-surface-deepest/80 backdrop-blur-xs flex items-start justify-center pt-16 px-4 animate-in fade-in duration-100"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-surface-elevated border border-border-primary rounded-xl shadow-2xl overflow-hidden flex flex-col font-sans select-none"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Input */}
        <div className="flex items-center gap-2 px-3.5 py-2.5 border-b border-border-subtle bg-surface-deepest/50">
          <span className="material-symbols-outlined text-[18px] text-text-muted">terminal</span>
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-[13px] text-text-primary placeholder-text-muted outline-none font-mono"
            placeholder="Type a command to run..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <span className="text-[10px] text-text-muted px-1.5 py-0.5 rounded bg-surface-hover border border-border-subtle font-mono">
            ESC to close
          </span>
        </div>

        {/* Command List */}
        <div ref={listRef} className="max-h-[360px] overflow-y-auto py-1.5 divide-y divide-border-subtle/30">
          {filtered.length > 0 ? (
            filtered.map((cmd, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  data-selected={isSelected}
                  className={`flex items-center justify-between px-3.5 py-2 cursor-pointer transition-colors text-[12px] ${
                    isSelected
                      ? 'bg-primary/15 text-text-primary border-l-2 border-primary'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  }`}
                  onClick={() => {
                    cmd.action();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <span className="material-symbols-outlined text-[16px] text-primary shrink-0">
                      {cmd.icon || 'play_circle'}
                    </span>
                    <span className="text-[10px] uppercase font-semibold text-text-muted tracking-wider shrink-0">
                      {cmd.category}
                    </span>
                    <span className="truncate font-medium">{cmd.title}</span>
                  </div>
                  {cmd.shortcut && (
                    <span className="text-[10px] text-text-muted font-mono px-1.5 py-0.5 rounded bg-surface-deepest border border-border-subtle shrink-0">
                      {cmd.shortcut}
                    </span>
                  )}
                </div>
              );
            })
          ) : (
            <div className="py-8 text-center text-text-muted text-[12px]">
              No matching commands found for &quot;{query}&quot;
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
