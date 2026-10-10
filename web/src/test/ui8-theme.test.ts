import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const sourceRoot = join(process.cwd(), 'src');
const tokenPath = join(sourceRoot, 'theme', 'tokens.css');
const css = readFileSync(tokenPath, 'utf8');
const parseTheme = (theme: 'dark' | 'light') => {
  const block = css.match(
    new RegExp(`:root\\[data-theme="${theme}"\\]\\s*\\{([\\s\\S]*?)\\n\\}`, 'm')
  )?.[1];
  if (!block) throw new Error(`Missing ${theme} theme token block`);
  return Object.fromEntries(
    Array.from(block.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g), ([, name, value]) => [
      name,
      value.trim(),
    ])
  );
};
const themes = { dark: parseTheme('dark'), light: parseTheme('light') };
const collect = (folder: string): string[] =>
  readdirSync(folder).flatMap((entry) => {
    const path = join(folder, entry);
    return statSync(path).isDirectory() ? collect(path) : [path];
  });

function color(value: string, backdrop = '#FFFFFF'): [number, number, number] {
  const hex = value.match(/^#([\da-f]{6})([\da-f]{2})?$/i);
  let rgb: number[];
  let alpha = 1;
  if (hex) {
    rgb = [0, 2, 4].map((offset) => parseInt(hex[1].slice(offset, offset + 2), 16));
    if (hex[2]) alpha = parseInt(hex[2], 16) / 255;
  } else {
    const rgba = value.match(
      /^rgba?\(\s*([\d.]+)[, ]+([\d.]+)[, ]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/i
    );
    if (!rgba) throw new Error(`Unsupported color token: ${value}`);
    rgb = [Number(rgba[1]), Number(rgba[2]), Number(rgba[3])];
    if (rgba[4])
      alpha = rgba[4].endsWith('%') ? Number(rgba[4].slice(0, -1)) / 100 : Number(rgba[4]);
  }
  if (alpha < 1) {
    const base = color(backdrop);
    rgb = rgb.map((channel, index) => channel * alpha + base[index] * (1 - alpha));
  }
  return rgb as [number, number, number];
}
const luminance = (rgb: number[]) =>
  rgb
    .map((v) => v / 255)
    .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
    .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
const contrast = (fg: string, bg: string, backdrop = '#FFFFFF') => {
  const a = luminance(color(fg));
  const b = luminance(color(bg, backdrop));
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
};

describe('UI-8 theme tokens', () => {
  it('defines the same token names in dark and light themes and resolves all source references', () => {
    expect(Object.keys(themes.light).sort()).toEqual(Object.keys(themes.dark).sort());
    const references = new Set(
      collect(sourceRoot).flatMap((path) =>
        Array.from(readFileSync(path, 'utf8').matchAll(/var\(\s*(--[\w-]+)/g), ([, name]) => name)
      )
    );
    for (const name of references) {
      expect(themes.dark, `missing ${name} in dark`).toHaveProperty(name);
      expect(themes.light, `missing ${name} in light`).toHaveProperty(name);
    }
  });

  it.each(['dark', 'light'] as const)('meets theme contrast requirements for %s', (themeName) => {
    const t = themes[themeName];
    const surface = (name: string) => t[`--${name}`];
    const check = (fg: string, bg: string, minimum = 4.5) =>
      expect(
        contrast(surface(fg), surface(bg)),
        `${themeName}: ${fg} on ${bg}`
      ).toBeGreaterThanOrEqual(minimum);
    for (const fg of ['text-primary', 'text-secondary', 'text-muted'])
      for (const bg of ['surface-1', 'surface-2', 'surface-3']) check(fg, bg);
    for (const bg of ['surface-1', 'surface-2', 'bg-accent']) check('text-accent', bg);
    for (const [fg, bg] of [
      ['text-success', 'bg-success'],
      ['text-warning', 'bg-warning'],
      ['text-danger', 'bg-danger'],
      ['text-neutral', 'bg-neutral'],
      ['diff-add-fg', 'diff-add-bg'],
      ['diff-del-fg', 'diff-del-bg'],
    ] as const) {
      const backdrop = bg.startsWith('diff-') ? surface('surface-1') : '#FFFFFF';
      expect(
        contrast(surface(fg), surface(bg), backdrop),
        `${themeName}: ${fg} on ${bg}`
      ).toBeGreaterThanOrEqual(4.5);
    }
    for (const fg of ['sev-critical', 'sev-high', 'sev-medium', 'sev-low', 'sev-info'])
      for (const bg of ['surface-1', 'surface-2']) check(fg, bg);
    check('tooltip-fg', 'tooltip-bg');
    check('focus-ring', 'surface-1', 3);
    check('focus-ring', 'surface-2', 3);
    check('border-control', 'surface-1', 3);
    check('border-control', 'surface-2', 3);
  });

  it('keeps palette colors in tokens instead of component code', () => {
    const colorLiteral =
      /(?:#[\da-f]{3,8}\b|\b(?:rgba?|hsla?)\s*\(|\b(?:color|background|backgroundColor|borderColor)\s*:\s*['"]?(?:black|white|red|green|blue|orange|yellow|purple|gray|grey)\b)/i;
    const violations = collect(sourceRoot)
      .filter(
        (path) =>
          path !== tokenPath &&
          !path.includes('test') &&
          !path.includes(`${join('theme', 'monacoTheme.ts')}`)
      )
      .flatMap((path) =>
        readFileSync(path, 'utf8')
          .split(/\r?\n/)
          .flatMap((line, index) => (colorLiteral.test(line) ? [`${path}:${index + 1}`] : []))
      );
    expect(violations).toEqual([]);
  });
});
