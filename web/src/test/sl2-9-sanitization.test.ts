import { describe, expect, it } from 'vitest';
import { sanitizeUntrustedText } from '../utils/sanitizeUntrusted';

describe('SL2-9 untrusted text handling', () => {
  it('preserves inert HTML and javascript-like text while removing terminal and bidi controls', () => {
    const hostile = '<img onerror="alert(1)"> javascript:alert(1)\u001b[31mred\u202e';
    const cleaned = sanitizeUntrustedText(hostile);
    expect(cleaned).toContain('<img onerror="alert(1)">');
    expect(cleaned).toContain('javascript:alert(1)');
    expect(cleaned).not.toContain('\u001b');
    expect(cleaned).not.toContain('\u202e');
  });
});
