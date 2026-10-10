import { useEffect } from 'react';

interface KeyboardShortcutOptions {
  onOpenPalette: () => void;
  onNextProblem: () => void;
  onPrevProblem: () => void;
  onAnalyze: () => void;
  onApplyQuickFix: () => void;
  onSave: () => void;
  onNewFile: () => void;
  onOpenFile: () => void;
  onCloseFile: () => void;
  onToggleFlyout: () => void;
  onCloseFlyout: () => void;
  isFlyoutOpen: boolean;
  onOpenShortcuts: () => void;
  isDirty: boolean;
}

export function useKeyboardShortcuts({
  onOpenPalette,
  onNextProblem,
  onPrevProblem,
  onAnalyze,
  onApplyQuickFix,
  onSave,
  onNewFile,
  onOpenFile,
  onCloseFile,
  onToggleFlyout,
  onCloseFlyout,
  isFlyoutOpen,
  onOpenShortcuts,
  isDirty,
}: KeyboardShortcutOptions): void {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const cmdOrCtrl = isMac ? event.metaKey : event.ctrlKey;

      if (cmdOrCtrl && event.shiftKey && event.key.toLowerCase() === 'p') {
        event.preventDefault();
        onOpenPalette();
        return;
      }

      if (event.key === 'F8') {
        event.preventDefault();
        if (event.shiftKey) onPrevProblem();
        else onNextProblem();
        return;
      }

      if (cmdOrCtrl && event.key === 'Enter') {
        event.preventDefault();
        onAnalyze();
        return;
      }

      if (cmdOrCtrl && event.key === '.') {
        event.preventDefault();
        onApplyQuickFix();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 's') {
        event.preventDefault();
        onSave();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'n') {
        event.preventDefault();
        onNewFile();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'o') {
        event.preventDefault();
        onOpenFile();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'w') {
        event.preventDefault();
        onCloseFile();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        onToggleFlyout();
        return;
      }

      if (event.key === 'Escape' && isFlyoutOpen) {
        event.preventDefault();
        onCloseFlyout();
        return;
      }

      if (
        event.key === '?' &&
        !cmdOrCtrl &&
        !event.altKey &&
        !(
          event.target instanceof HTMLElement &&
          (event.target.isContentEditable || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName))
        )
      ) {
        onOpenShortcuts();
        return;
      }
    };

    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (isDirty) {
        event.preventDefault();
        event.returnValue = '';
      }
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('beforeunload', onBeforeUnload);
    };
  }, [
    onOpenPalette,
    onNextProblem,
    onPrevProblem,
    onAnalyze,
    onApplyQuickFix,
    onSave,
    onNewFile,
    onOpenFile,
    onCloseFile,
    onToggleFlyout,
    onCloseFlyout,
    isFlyoutOpen,
    onOpenShortcuts,
    isDirty,
  ]);
}
