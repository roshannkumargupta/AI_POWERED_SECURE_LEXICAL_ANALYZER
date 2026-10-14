import { fireEvent, render, screen } from '@testing-library/react';
import { useRef, useState } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { closeOnBackdrop, useModalBehavior } from './modalBehavior';

function ModalHarness({ onClose }: { onClose: () => void }) {
  const [open, setOpen] = useState(false);
  const close = () => {
    onClose();
    setOpen(false);
  };
  return (
    <>
      <button onClick={() => setOpen(true)}>Invoker</button>
      {open && (
        <div className="backdrop" onMouseDown={(event) => closeOnBackdrop(event, close)}>
          <ModalContent onClose={close} />
        </div>
      )}
    </>
  );
}
function ModalContent({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLElement>(null);
  useModalBehavior(true, ref, onClose);
  return (
    <section ref={ref} role="dialog" aria-modal="true" tabIndex={-1}>
      <button>First</button>
      <button>Last</button>
    </section>
  );
}

describe('shared modal behavior', () => {
  it('closes on Escape, traps focus and restores the invoking control', async () => {
    const onClose = vi.fn();
    render(<ModalHarness onClose={onClose} />);
    const invoker = screen.getByRole('button', { name: 'Invoker' });
    invoker.focus();
    fireEvent.click(invoker);
    const first = screen.getByRole('button', { name: 'First' });
    const last = screen.getByRole('button', { name: 'Last' });
    last.focus();
    fireEvent.keyDown(window, { key: 'Tab' });
    expect(first).toHaveFocus();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
    expect(invoker).toHaveFocus();
  });

  it('closes only when the backdrop itself receives the pointer event', () => {
    const onClose = vi.fn();
    const { container } = render(<ModalHarness onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: 'Invoker' }));
    fireEvent.mouseDown(screen.getByRole('dialog'));
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.mouseDown(container.querySelector('.backdrop')!);
    expect(onClose).toHaveBeenCalledOnce();
  });
});
