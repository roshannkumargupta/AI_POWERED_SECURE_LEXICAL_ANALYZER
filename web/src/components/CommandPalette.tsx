import React from 'react';
import { Search, X } from 'lucide-react';

export interface PaletteCommand { label: string; run: () => void; keywords?: string }

export const CommandPalette: React.FC<{ open: boolean; commands: PaletteCommand[]; onClose: () => void }> = ({ open, commands, onClose }) => {
  const [query, setQuery] = React.useState('');
  const [active, setActive] = React.useState(0);
  const input = React.useRef<HTMLInputElement>(null);
  const visible = commands.map((command, index) => ({ command, index, score: fuzzyScore(`${command.label} ${command.keywords || ''}`, query) })).filter((item) => item.score >= 0).sort((a, b) => b.score - a.score);
  React.useEffect(() => { if (open) { setQuery(''); setActive(0); requestAnimationFrame(() => input.current?.focus()); } }, [open]);
  if (!open) return null;
  const choose = () => { visible[active]?.command.run(); onClose(); };
  return <div style={overlay} onMouseDown={onClose}>
    <div role="dialog" aria-label="Command palette" style={dialog} onMouseDown={(event) => event.stopPropagation()}>
      <div style={searchRow}><Search size={16}/><input ref={input} aria-label="Filter commands" value={query} onChange={(event) => { setQuery(event.target.value); setActive(0); }} onKeyDown={(event) => {
        if (event.key === 'Escape') onClose();
        if (event.key === 'ArrowDown') { event.preventDefault(); setActive((i) => Math.min(i + 1, visible.length - 1)); }
        if (event.key === 'ArrowUp') { event.preventDefault(); setActive((i) => Math.max(i - 1, 0)); }
        if (event.key === 'Enter') choose();
      }} placeholder="Type a command…"/><button aria-label="Close palette" onClick={onClose}><X size={15}/></button></div>
      <div role="listbox" aria-label="Commands" style={{ maxHeight: 330, overflow: 'auto' }}>{visible.map(({ command }, visibleIndex) => <button role="option" aria-selected={visibleIndex === active} key={command.label} onMouseEnter={() => setActive(visibleIndex)} onClick={() => { command.run(); onClose(); }} style={{ ...item, background: visibleIndex === active ? 'var(--panel-3)' : 'transparent' }}>{command.label}</button>)}</div>
      {!visible.length && <div style={{ padding: 12, color: 'var(--muted)' }}>No matching commands</div>}
    </div>
  </div>;
};

function fuzzyScore(text: string, query: string): number {
  if (!query.trim()) return 1;
  const needle = query.toLowerCase().replace(/\s+/g, ''); let at = 0; let score = 0;
  for (const char of needle) { const found = text.toLowerCase().indexOf(char, at); if (found < 0) return -1; score += found === at ? 2 : 1; at = found + 1; }
  return score;
}
const overlay: React.CSSProperties = { position: 'fixed', inset: 0, zIndex: 200, background: 'var(--scrim)', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', paddingTop: '12vh' };
const dialog: React.CSSProperties = { width: 560, maxWidth: '90vw', background: 'var(--panel)', border: '1px solid var(--border)', borderRadius: 6, boxShadow: 'var(--shadow-popover)', overflow: 'hidden' };
const searchRow: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderBottom: '1px solid var(--border)', color: 'var(--muted)' };
const item: React.CSSProperties = { display: 'block', width: '100%', textAlign: 'left', padding: '8px 14px', color: 'var(--text)', fontSize: 13 };
