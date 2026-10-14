import { useRef } from 'react';
import type { Command } from '../state/commands';
import { closeOnBackdrop, useModalBehavior } from '../lib/modalBehavior';

export function ShortcutsDialog({
  open,
  commands,
  onClose,
}: {
  open: boolean;
  commands: Command[];
  onClose(): void;
}) {
  const dialog = useRef<HTMLElement>(null);
  useModalBehavior(open, dialog, onClose);
  if (!open) return null;
  return (
    <div
      className="ide-overlay ide-modal-overlay"
      onMouseDown={(event) => closeOnBackdrop(event, onClose)}
    >
      <section
        ref={dialog}
        className="ide-dialog ide-shortcuts-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard Shortcuts"
        tabIndex={-1}
      >
        <header>
          <h2>Keyboard Shortcuts</h2>
          <button type="button" aria-label="Close Keyboard Shortcuts" onClick={onClose}>
            ×
          </button>
        </header>
        <div className="ide-shortcuts-list">
          {commands
            .filter((command) => command.keybinding)
            .map((command) => (
              <div key={command.id}>
                <span>{command.title}</span>
                <kbd>{command.keybinding}</kbd>
              </div>
            ))}
        </div>
      </section>
    </div>
  );
}
