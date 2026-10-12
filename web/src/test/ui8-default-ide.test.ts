import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('P8 default IDE and offline workers', () => {
  it('renders the IDE unconditionally and initializes bundled Monaco workers before React', () => {
    const main = readFileSync(resolve(process.cwd(), 'src/main.tsx'), 'utf8');
    expect(main).not.toContain("get('ui') === 'new'");
    expect(main).toContain('<IDE />');
    expect(main.indexOf('initIDEWorkers();')).toBeLessThan(main.indexOf('ReactDOM.createRoot'));
    expect(main).toContain("from './ide/lib/monacoWorkers'");
  });
});
