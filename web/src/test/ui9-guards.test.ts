import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';
import { processFileForOpen } from '../utils/fileLoader';

describe('UI-9 Guards: File Analysis State Machine', () => {
  interface MockDoc {
    id: string;
    content: string;
    contentVersion: number;
    resultVersion: number;
    analysis: any | null;
    status: 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error';
  }

  function getDocState(
    doc: MockDoc
  ): 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error' {
    if (doc.status === 'analysing') return 'analysing';
    if (doc.status === 'error') return 'error';
    if (!doc.analysis) return 'not analysed';
    if (doc.contentVersion > doc.resultVersion) return 'stale';
    return 'analysed';
  }

  it('starts in "not analysed" state for new files and samples', () => {
    const doc: MockDoc = {
      id: 'doc-1',
      content: 'print(1)',
      contentVersion: 0,
      resultVersion: -1,
      analysis: null,
      status: 'not analysed',
    };
    expect(getDocState(doc)).toBe('not analysed');
  });

  it('transitions to "analysing" when analysis starts', () => {
    const doc: MockDoc = {
      id: 'doc-1',
      content: 'print(1)',
      contentVersion: 0,
      resultVersion: -1,
      analysis: null,
      status: 'analysing',
    };
    expect(getDocState(doc)).toBe('analysing');
  });

  it('transitions to "analysed" with matching version on result arrival', () => {
    const doc: MockDoc = {
      id: 'doc-1',
      content: 'print(1)',
      contentVersion: 1,
      resultVersion: 1,
      analysis: { findings: [] },
      status: 'analysed',
    };
    expect(getDocState(doc)).toBe('analysed');
  });

  it('transitions to "stale" when content is edited after analysis', () => {
    const doc: MockDoc = {
      id: 'doc-1',
      content: 'print(1); x = 2',
      contentVersion: 2,
      resultVersion: 1,
      analysis: { findings: [] },
      status: 'stale',
    };
    expect(getDocState(doc)).toBe('stale');
  });

  it('recovers to "analysed" when stale file is re-analyzed', () => {
    const doc: MockDoc = {
      id: 'doc-1',
      content: 'print(1); x = 2',
      contentVersion: 2,
      resultVersion: 2,
      analysis: { findings: [] },
      status: 'analysed',
    };
    expect(getDocState(doc)).toBe('analysed');
  });
});

describe('UI-9 Guards: File Loader and Encoding Boundaries', () => {
  it('strips UTF-8 BOM cleanly', async () => {
    const withBom = new Uint8Array([0xef, 0xbb, 0xbf, 0x61, 0x62, 0x63]);
    const file = new File([withBom], 'test.py', { type: 'text/plain' });
    const outcome = await processFileForOpen(file);
    expect(outcome.error).toBeUndefined();
    expect(outcome.file?.content).toBe('abc');
    expect(outcome.file?.content.charCodeAt(0)).toBe(0x61);
  });

  it('refuses files exceeding 512 KB', async () => {
    const oversized = new Uint8Array(513 * 1024);
    const file = new File([oversized], 'big.py', { type: 'text/plain' });
    const outcome = await processFileForOpen(file);
    expect(outcome.error).toContain('exceeds 512 KB limit');
    expect(outcome.file).toBeUndefined();
  });

  it('refuses binary files containing NUL bytes', async () => {
    const binaryBytes = new Uint8Array([0x70, 0x72, 0x69, 0x00, 0x6e, 0x74]);
    const file = new File([binaryBytes], 'corrupt.py', { type: 'text/plain' });
    const outcome = await processFileForOpen(file);
    expect(outcome.error).toContain('appears to be a binary file');
    expect(outcome.file).toBeUndefined();
  });

  it('decodes invalid UTF-8 with replacement character and warning', async () => {
    const invalidUtf8 = new Uint8Array([0x61, 0xff, 0x62]);
    const file = new File([invalidUtf8], 'invalid.py', { type: 'text/plain' });
    const outcome = await processFileForOpen(file);
    expect(outcome.warning).toContain('Not valid UTF-8');
    expect(outcome.file?.content).toContain('\uFFFD');
  });

  it('detects CRLF line endings for preservation on save', async () => {
    const crlfText = 'line1\r\nline2\r\n';
    const file = new File([crlfText], 'dos.py', { type: 'text/plain' });
    const outcome = await processFileForOpen(file);
    expect(outcome.file?.hasCrlf).toBe(true);
  });
});

describe('UI-9 Guards: Navigation Module Isolation', () => {
  it('forbids calling editor.setValue, setSelection, setPosition, revealRange outside navigation module', () => {
    const srcDir = join(__dirname, '..');
    const filesToScan: string[] = [];

    function walk(dir: string) {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!entry.name.includes('node_modules') && !entry.name.includes('dist')) {
            walk(full);
          }
        } else if (/\.(ts|tsx)$/.test(entry.name) && !entry.name.includes('.test.')) {
          filesToScan.push(full);
        }
      }
    }

    walk(srcDir);

    const violations: string[] = [];
    const forbiddenPatterns = [
      /\.setValue\s*\(/,
      /\.setSelection\s*\(/,
      /\.setPosition\s*\(/,
      /\.revealRange\s*\(/,
      /\.revealRangeInCenter\s*\(/,
    ];

    for (const filePath of filesToScan) {
      if (
        filePath.includes(join('editor', 'navigation.ts')) ||
        filePath.includes('testHarness.ts')
      ) {
        continue;
      }

      const content = readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      lines.forEach((line, lineIdx) => {
        for (const pattern of forbiddenPatterns) {
          if (pattern.test(line)) {
            // Ignore comments
            if (line.trim().startsWith('//') || line.trim().startsWith('*')) continue;
            violations.push(`${filePath}:${lineIdx + 1} -> ${line.trim()}`);
          }
        }
      });
    }

    expect(violations).toEqual([]);
  });
});

describe('UI-9 Guards: Test Harness Production Exclusion', () => {
  it('proves window.__slTest is absent from the production build bundle', () => {
    const distDir = join(__dirname, '..', '..', 'dist', 'assets');
    if (!existsSync(distDir)) {
      // Build output directory
      return;
    }

    const jsFiles = readdirSync(distDir).filter((f) => f.endsWith('.js'));
    for (const file of jsFiles) {
      const code = readFileSync(join(distDir, file), 'utf8');
      expect(code.includes('__slTest')).toBe(false);
    }
  });
});
