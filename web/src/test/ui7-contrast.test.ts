import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const sourceRoot = join(process.cwd(), 'src');
const collect = (folder: string): string[] => readdirSync(folder).flatMap((entry) => {
  const path = join(folder, entry);
  return statSync(path).isDirectory() ? collect(path) : [path];
});
const srgb = (value: number) => { const channel = value / 255; return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4; };
const luminance = (hex: string) => { const rgb = hex.slice(1).match(/.{2}/g)!.map((part) => parseInt(part, 16)); return 0.2126 * srgb(rgb[0]) + 0.7152 * srgb(rgb[1]) + 0.0722 * srgb(rgb[2]); };
const ratio = (foreground: string, background: string) => { const a = luminance(foreground); const b = luminance(background); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); };

describe('UI-7 theme guards', () => {
  it('keeps hard-coded pure black colors out of application source', () => {
    // Monaco's #00000000 editorLineHighlightBorder is transparent and retained
    // in monacoTheme.ts as an intentional editor-theme exception.
    const forbidden = /#000(?:000)?\b|\bblack\b|rgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:[,)]|\/)|hsl\(\s*0\s+0%\s+0%/i;
    const violations = collect(sourceRoot)
      .filter((path) => !path.includes(`${join('theme', 'monacoTheme.ts')}`) && !path.includes(`${join('test', 'ui7-contrast.test.ts')}`) && !path.includes(`${join('test', 'ui8-theme.test.ts')}`))
      .flatMap((path) => readFileSync(path, 'utf8').split(/\r?\n/).flatMap((line, index) => forbidden.test(line) ? [`${path}:${index + 1}`] : []));
    expect(violations).toEqual([]);
  });

  it('keeps documented text and status token pairs at WCAG AA contrast', () => {
    const pairs: Array<[string, string]> = [
      ['#F0EFEC', '#151515'], ['#C3C2B7', '#151515'], ['#898781', '#151515'],
      ['#6DA7EC', '#151515'], ['#0CA30C', '#11260F'], ['#DB9300', '#311A00'],
      ['#EC7E7E', '#3C0E0E'],
    ];
    for (const [foreground, background] of pairs) expect(ratio(foreground, background)).toBeGreaterThanOrEqual(4.5);
  });
});
