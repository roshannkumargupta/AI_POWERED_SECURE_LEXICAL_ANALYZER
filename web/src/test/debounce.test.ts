import { describe, it, expect, vi } from 'vitest';

export function debounce<T extends (...args: any[]) => void>(
  fn: T,
  delayMs: number
): { (...args: Parameters<T>): void; cancel: () => void } {
  let timer: any = null;

  const debounced = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn(...args);
    }, delayMs);
  };

  debounced.cancel = () => {
    if (timer) clearTimeout(timer);
  };

  return debounced;
}

describe('Debounce Behavior', () => {
  it('delays execution and collapses rapid successive calls', () => {
    vi.useFakeTimers();
    const callback = vi.fn();
    const debouncedFn = debounce(callback, 600);

    // Call 5 times rapidly
    debouncedFn('call 1');
    debouncedFn('call 2');
    debouncedFn('call 3');
    debouncedFn('call 4');
    debouncedFn('call 5');

    expect(callback).not.toHaveBeenCalled();

    // Fast-forward 500 ms (still within debounce window)
    vi.advanceTimersByTime(500);
    expect(callback).not.toHaveBeenCalled();

    // Advance remaining 100 ms
    vi.advanceTimersByTime(100);
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('call 5');

    vi.useRealTimers();
  });

  it('allows canceling in-flight debounced invocation', () => {
    vi.useFakeTimers();
    const callback = vi.fn();
    const debouncedFn = debounce(callback, 600);

    debouncedFn('pending call');
    vi.advanceTimersByTime(300);

    debouncedFn.cancel();
    vi.advanceTimersByTime(500);

    expect(callback).not.toHaveBeenCalled();
    vi.useRealTimers();
  });
});
