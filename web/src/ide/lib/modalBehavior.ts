import { useEffect, useRef, type MouseEvent, type RefObject } from 'react';

/** Shared keyboard, focus and backdrop behavior for IDE dialogs and drawers. */
export function useModalBehavior(
  open: boolean,
  container: RefObject<HTMLElement | null>,
  onClose: () => void
) {
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    if (!open) return;
    const previouslyFocused =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const focusable = () =>
      Array.from(
        container.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href],[tabindex="0"]'
        ) ?? []
      );
    requestAnimationFrame(() => (focusable()[0] ?? container.current)?.focus());
    const keydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopImmediatePropagation();
        closeRef.current();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = focusable();
      if (!items.length) {
        event.preventDefault();
        container.current?.focus();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (
        event.shiftKey &&
        (document.activeElement === first || !container.current?.contains(document.activeElement))
      ) {
        event.preventDefault();
        last.focus();
      } else if (
        !event.shiftKey &&
        (document.activeElement === last || !container.current?.contains(document.activeElement))
      ) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener('keydown', keydown);
    return () => {
      window.removeEventListener('keydown', keydown);
      previouslyFocused?.focus();
    };
  }, [open, container]);
}

export function closeOnBackdrop(event: MouseEvent<HTMLElement>, onClose: () => void) {
  if (event.target === event.currentTarget) onClose();
}
