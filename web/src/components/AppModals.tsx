import React from 'react';
import { CommandPalette, PaletteCommand } from './CommandPalette';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import { DiffView } from './DiffView';
import { ReviewFixesModal, ReviewFixItem } from './ReviewFixesModal';
import { ToastContainer } from './Toast';
import { AppState, ToastItem } from '../state/store';

interface AppModalsProps {
  paletteOpen: boolean;
  onClosePalette: () => void;
  commands: PaletteCommand[];
  shortcutsOpen: boolean;
  onCloseShortcuts: () => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  directoryInputRef: React.RefObject<HTMLInputElement>;
  onFilesSelected: (files: File[]) => Promise<void>;
  onDirectoryFilesSelected: (files: File[]) => Promise<void>;
  diffModal: AppState['diffModal'];
  onApplyDiffFix: () => void;
  onCloseDiffModal: () => void;
  reviewFixesOpen: boolean;
  reviewFixItems: ReviewFixItem[];
  onCloseReviewFixes: () => void;
  onApplySelectedReviewFixes: (selectedFixes: ReviewFixItem[]) => void;
  toasts: ToastItem[];
  onDismissToast: (id: string) => void;
}

export const AppModals: React.FC<AppModalsProps> = ({
  paletteOpen,
  onClosePalette,
  commands,
  shortcutsOpen,
  onCloseShortcuts,
  fileInputRef,
  directoryInputRef,
  onFilesSelected,
  onDirectoryFilesSelected,
  diffModal,
  onApplyDiffFix,
  onCloseDiffModal,
  reviewFixesOpen,
  reviewFixItems,
  onCloseReviewFixes,
  onApplySelectedReviewFixes,
  toasts,
  onDismissToast,
}) => {
  return (
    <>
      <CommandPalette open={paletteOpen} onClose={onClosePalette} commands={commands} />

      <KeyboardShortcutsModal isOpen={shortcutsOpen} onClose={onCloseShortcuts} />

      {/* Hidden File Input for Open File */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".py,.java,.js,.mjs,.cjs,.jsx,.c,.h,.cc,.cpp,.cxx,.hpp"
        style={{ display: 'none' }}
        onChange={async (event) => {
          const files = Array.from(event.target.files || []);
          await onFilesSelected(files);
          event.currentTarget.value = '';
        }}
      />

      {/* Hidden Directory Input for Open Folder */}
      <input
        ref={directoryInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        {...({ webkitdirectory: '', directory: '' } as React.InputHTMLAttributes<HTMLInputElement>)}
        onChange={async (event) => {
          const files = Array.from(event.currentTarget.files || []);
          await onDirectoryFilesSelected(files);
          event.currentTarget.value = '';
        }}
      />

      {/* Diff Review Modal */}
      {diffModal && diffModal.fix && diffModal.finding && (
        <DiffView
          isOpen={diffModal.isOpen}
          fix={diffModal.fix}
          finding={diffModal.finding}
          diff={diffModal.diff}
          before={diffModal.oldSource}
          after={diffModal.newSource}
          onApply={onApplyDiffFix}
          onCancel={onCloseDiffModal}
        />
      )}

      {/* Review Fixes Modal */}
      <ReviewFixesModal
        isOpen={reviewFixesOpen}
        fixes={reviewFixItems}
        onClose={onCloseReviewFixes}
        onApplySelected={onApplySelectedReviewFixes}
      />

      <ToastContainer toasts={toasts} onDismiss={onDismissToast} />
    </>
  );
};
