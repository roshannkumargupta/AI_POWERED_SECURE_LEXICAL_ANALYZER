import { describe, expect, it } from 'vitest';
import { findEnclosingSymbol } from '../utils/breadcrumbs';
import { findingCategory } from '../utils/findingCategory';

describe('UI-2 breadcrumbs', () => {
  it.each([
    ['python', 'def a():\n  pass', 'a'],
    ['python', 'class B:\n  def c(self):\n    pass', 'c'],
    ['javascript', 'function a() {\n return 1;\n}', 'a'],
    ['javascript', 'const b = (x) => {\n return x;\n}', 'b'],
    ['java', 'class A {\n void run() {\n }\n}', 'run'],
    ['java', 'class A {\n int sum(int a) {\n return a;\n }\n}', 'sum'],
    ['cpp', 'class A {\n void run() {\n }\n};', 'run'],
    ['cpp', 'int main() {\n return 0;\n}', 'main'],
    ['python', 'async def work():\n  await go()', 'work'],
    ['javascript', 'const named = async (x) => x;', 'named'],
    ['python', 'def alpha():\n return 1', 'alpha'],
    ['python', 'def beta(x):\n return x', 'beta'],
    ['python', 'class Gamma:\n pass', 'Gamma'],
    ['python', 'async def delta():\n pass', 'delta'],
    ['python', 'def epsilon():\n pass', 'epsilon'],
    ['python', 'class Zeta(Base):\n pass', 'Zeta'],
    ['python', 'async def theta(x):\n pass', 'theta'],
    ['javascript', 'function bravo() {\n return 1;\n}', 'bravo'],
    ['javascript', 'const charlie = x => x;', 'charlie'],
    ['javascript', 'let delta = async () => 1;', 'delta'],
    ['javascript', 'var echo = (a, b) => a + b;', 'echo'],
    ['javascript', 'export function foxtrot() {\n}', 'foxtrot'],
    ['javascript', 'const golf = (x) => {\n return x;\n}', 'golf'],
    ['javascript', 'async function hotel() {\n}', 'hotel'],
    ['java', 'public void alpha() {\n}', 'alpha'],
    ['java', 'private int beta(int x) {\n}', 'beta'],
    ['java', 'static String gamma() {\n}', 'gamma'],
    ['java', 'protected boolean delta() {\n}', 'delta'],
    ['java', 'public long epsilon(long n) {\n}', 'epsilon'],
    ['java', 'synchronized void zeta() {\n}', 'zeta'],
    ['java', 'static final int eta() {\n}', 'eta'],
    ['java', 'private double theta() {\n}', 'theta'],
    ['cpp', 'void alpha() {\n}', 'alpha'],
    ['cpp', 'int beta(int x) {\n return x;\n}', 'beta'],
    ['cpp', 'static bool gamma() {\n}', 'gamma'],
    ['cpp', 'unsigned long delta() {\n}', 'delta'],
    ['cpp', 'virtual void epsilon() {\n}', 'epsilon'],
    ['cpp', 'auto zeta() {\n}', 'zeta'],
    ['cpp', 'long eta(long n) {\n}', 'eta'],
    ['cpp', 'double theta() {\n}', 'theta'],
  ])('%s finds an enclosing symbol', (language, source, expected) => {
    expect(findEnclosingSymbol(source, language, 2)?.label).toBe(expected);
  });
  it('omits a symbol when no best-effort match exists', () =>
    expect(findEnclosingSymbol('x = 2', 'python', 1)).toBeNull());
});

describe('findingCategory', () => {
  it.each([
    ['CWE-78', 'Command Injection'],
    ['CWE-89', 'SQL Injection'],
    ['CWE-79', 'XSS'],
    ['CWE-502', 'Unsafe Deserialization'],
    ['CWE-327', 'Weak Crypto'],
    ['CWE-798', 'Hard-coded Secret'],
    ['CWE-22', 'Path Traversal'],
    ['CWE-787', 'Memory Safety'],
    ['CWE-611', 'XXE'],
    ['CWE-918', 'Network Security'],
    ['CWE-1007', 'Unicode Security'],
  ])('%s maps to %s', (cwe, expected) => {
    expect(findingCategory({ cwe, rule_id: 'RULE_FALLBACK' } as never)).toBe(expected);
  });
  it('uses rule category when CWE is unknown', () =>
    expect(findingCategory({ cwe: 'CWE-9999', rule_id: 'SEC-ABC' } as never)).toBe('SEC'));
});
