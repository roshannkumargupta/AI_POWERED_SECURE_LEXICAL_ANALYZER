import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('P8 default IDE and offline workers', () => {
  it('renders the IDE unconditionally and initializes bundled Monaco workers before the editor', () => {
    const main = readFileSync(resolve(process.cwd(), 'src/main.tsx'), 'utf8');
    const editor = readFileSync(resolve(process.cwd(), 'src/ide/lib/MonacoEditor.tsx'), 'utf8');
    expect(main).not.toContain("get('ui') === 'new'");
    expect(main).toContain('<IDE />');
    expect(editor.indexOf('initIDEWorkers();')).toBeLessThan(
      editor.indexOf('export default Editor')
    );
    expect(editor).toContain("from './monacoWorkers'");
  });
});
