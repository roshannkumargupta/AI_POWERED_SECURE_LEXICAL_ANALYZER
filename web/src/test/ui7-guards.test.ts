import { describe, expect, it } from 'vitest';
import { computeUiScale, monacoMetrics } from '../utils/uiScale';

describe('UI-7 guards', () => {
  it('keeps normal interface sizing across viewport resolutions', () => {
    expect(computeUiScale(1536, 1022)).toBe(1);
    expect(computeUiScale(1366, 768)).toBe(1);
    expect(computeUiScale(1280, 720)).toBe(1);
    expect(computeUiScale(1920, 1080)).toBe(1);
    expect(computeUiScale(600, 900)).toBe(1);
    expect(computeUiScale(1536, 1022, 0.85)).toBe(0.85);
    expect(computeUiScale(1536, 1022, 1.15)).toBe(1.15);
  });

  it('maps Monaco size and line height to the chosen interface scale', () => {
    expect(monacoMetrics(2)).toEqual({ fontSize: 24, lineHeight: 48 });
    expect(monacoMetrics(1.5, 0.85)).toEqual({ fontSize: 15, lineHeight: 31 });
  });
});
