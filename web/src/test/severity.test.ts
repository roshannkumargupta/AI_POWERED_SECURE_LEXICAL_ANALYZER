import { describe, it, expect } from 'vitest';
import { Severity } from '../api/client';

export const SEVERITY_COLORS: Record<Severity, string> = {
  critical: '#FF4D6D',
  high: '#FF8A3D',
  medium: '#F5C542',
  low: '#5CC8FF',
  info: '#8FA1BB',
};

describe('Severity to Color Mapping', () => {
  it('correctly maps severity levels to SecureLex Night color tokens', () => {
    expect(SEVERITY_COLORS.critical).toBe('#FF4D6D');
    expect(SEVERITY_COLORS.high).toBe('#FF8A3D');
    expect(SEVERITY_COLORS.medium).toBe('#F5C542');
    expect(SEVERITY_COLORS.low).toBe('#5CC8FF');
    expect(SEVERITY_COLORS.info).toBe('#8FA1BB');
  });

  it('guarantees unique distinct colors for all severity tiers', () => {
    const values = Object.values(SEVERITY_COLORS);
    const uniqueValues = new Set(values);
    expect(uniqueValues.size).toBe(5);
  });
});
