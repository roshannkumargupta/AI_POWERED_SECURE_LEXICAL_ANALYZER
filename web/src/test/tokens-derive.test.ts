import { describe, expect, it } from 'vitest';
import python from '../../../docs/api_samples/analyze_python.json';
import java from '../../../docs/api_samples/analyze_java.json';
import type { AnalysisResult } from '../api/client';
import { deriveTokens, lexicalType, visibleTokenText } from '../tokens/derive';

describe('token security derivation', () => {
  it('maps all kinds observed in Python and Java API responses', () => {
    const kinds = [...new Set([...python.tokens, ...java.tokens].map((t) => t.token_type))];
    expect(kinds.filter((kind) => lexicalType(kind) === 'Other')).toEqual([]);
    const javascript=['COMMENT','IDENTIFIER','KEYWORD','NUMBER','OPERATOR','PUNCTUATION','WHITESPACE'];
    const cpp=['IDENTIFIER','KEYWORD','NUMBER','OPERATOR','PREPROCESSOR','WHITESPACE'];
    expect(javascript.filter((kind)=>lexicalType(kind)==='Other')).toEqual([]);
    expect(cpp.filter((kind)=>lexicalType(kind)==='Other')).toEqual(['PREPROCESSOR']);
  });
  it('connects the Flask source, propagation and sink ranges in order', () => {
    const tokens = deriveTokens(python as unknown as AnalysisResult);
    const tainted = tokens.filter((token) => token.detectors.includes('Taint'));
    expect(tainted.some((token) => token.role === 'Source')).toBe(true);
    expect(tainted.some((token) => token.role === 'Propagation')).toBe(true);
    expect(tainted.some((token) => token.role === 'Sink' || token.role === 'Dangerous API')).toBe(true);
    expect(tainted.map((token) => token.range.start_line)).toEqual([...tainted].map((t) => t.range.start_line).sort((a,b)=>a-b));
  });
  it('memoizes derivation and makes control characters visible', () => {
    const data = python as unknown as AnalysisResult;
    expect(deriveTokens(data)).toBe(deriveTokens(data));
    expect(visibleTokenText('x\u202ey')).toBe('x<U+202E>y');
  });
  it('keeps plain safe tokens neutral and maps unknown kinds to Other', () => {
    expect(lexicalType('WHITESPACE')).toBe('Whitespace');
    expect(lexicalType('UNSEEN_KIND')).toBe('Other');
    const safe = { ...(python as unknown as AnalysisResult), findings: [], tokens: [{ token:'name', token_type:'IDENTIFIER', range:{start_line:1,start_col:1,end_line:1,end_col:5}, label:'SAFE', score:0 }] };
    expect(deriveTokens(safe).filter((token)=>token.securityRelevant)).toHaveLength(0);
  });
  it('derives 5,000 tokens under the UI budget', () => {
    const base=python as unknown as AnalysisResult;
    const result:AnalysisResult={...base,findings:[{...base.findings[0],range:{start_line:1,start_col:1,end_line:1,end_col:10001},taint_path:[]}],tokens:Array.from({length:5000},(_,i)=>({token:'x',token_type:'IDENTIFIER',range:{start_line:1,start_col:i*2+1,end_line:1,end_col:i*2+2},label:'SAFE',score:0}))};
    const started=performance.now(); const derived=deriveTokens(result); const elapsed=performance.now()-started;
    console.info(`UI-3 derive performance: 5,000 tokens in ${elapsed.toFixed(2)} ms`);
    expect(derived).toHaveLength(5000); expect(elapsed).toBeLessThan(100);
  });
});
