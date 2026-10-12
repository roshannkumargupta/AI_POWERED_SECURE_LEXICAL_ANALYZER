import { describe, expect, it } from 'vitest';
import { readAutoAnalyze, writeAutoAnalyze } from './preferences';

describe('settings persistence', () => {
  it('round trips analyze-while-typing and tolerates storage failures', () => {
    const values = new Map<string, string>();
    const storage = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => { values.set(key, value); } };
    expect(readAutoAnalyze(storage)).toBe(false);
    writeAutoAnalyze(true, storage);
    expect(readAutoAnalyze(storage)).toBe(true);
    const broken = { getItem: () => { throw new Error('blocked'); }, setItem: () => { throw new Error('blocked'); } };
    expect(readAutoAnalyze(broken)).toBe(false);
    expect(() => writeAutoAnalyze(false, broken)).not.toThrow();
  });
});
