import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { adaptTokens, confidenceText, explanationText, findingGroup, foundBy, mapTokenType, mergeLexemes, typeLabel, visibleText } from '../model/adapt';
import type { AnalysisResult, Finding, TokenInfo } from '../api/client';

const sample=(name:string)=>JSON.parse(readFileSync(resolve(process.cwd(),'../docs/api_samples',name),'utf8')) as AnalysisResult;
const token=(text:string,kind:string,line=1,col=1):TokenInfo=>({token:text,token_type:kind,range:{start_line:line,start_col:col,end_line:line,end_col:col+text.length},label:'SAFE',score:0});
const finding=(extra:Partial<Finding>={}):Finding=>({id:'f1',rule_id:'APS-PY-INJ-002',title:'Command injection',cwe:'CWE-78',severity:'high',label:'MALICIOUS',confidence:.97,range:{start_line:1,start_col:1,end_line:1,end_col:10},message:'risk',explanation:'Unsafe sink.',evidence:{confidence_breakdown:{rule_score:.8,ml_score:.88,ml_mode:'on',rule_weight:.7,ml_weight:.3,taint_bonus:.15,taint_confirmed:true,fused:.97}},taint_path:[],fixes:[],sources:['rule','taint'],...extra});
describe('UI-5 token adapter',()=>{
  it('maps actual language samples and tolerates unknown kinds',()=>{for(const file of ['analyze_python.json','analyze_java.json','analyze_javascript.json','analyze_c.json']){const result=sample(file);expect(adaptTokens(result).length).toBeGreaterThan(0);for(const t of result.tokens)expect(mapTokenType(t.token_type)).toBeTruthy();}expect(mapTokenType('FUTURE_KIND')).toBe('OTHER');});
  it('drops whitespace and merges dotted and namespace calls while preserving raw ids',()=>{const rows=mergeLexemes([token('os','IDENTIFIER'),token(' ','WHITESPACE',1,3),token('.','OPERATOR',1,4),token('system','IDENTIFIER',1,5),token('(','PUNCTUATION',1,11)]);expect(rows.map(r=>r.lexeme)).toEqual(['os.system','(']);expect(rows[0].type).toBe('CALL');expect(rows[0].rawTokenIds).toEqual(['token-0','token-2','token-3']);});
  it('marks only overlapping primary ranges insecure and prioritizes severity',()=>{const result={tokens:[token('user','IDENTIFIER'),token('system','IDENTIFIER',1,20)],findings:[finding({id:'source',range:{start_line:1,start_col:1,end_line:1,end_col:5},taint_path:[{step:'source',range:{start_line:1,start_col:1,end_line:1,end_col:5},text:'user',note:''}]}),finding({id:'sink',range:{start_line:1,start_col:20,end_line:1,end_col:26}})]} as AnalysisResult;const rows=adaptTokens(result);expect(rows[0].security).toBe('insecure');expect(rows[1].security).toBe('insecure');expect(rows[1].primaryFindingId).toBe('sink');});
  it('groups a high DOM XSS rule as Dangerous and only uses Malicious for an explicit tag',()=>{
    const domXss=finding({rule_id:'APS-JS-XSS-001',title:'DOM XSS',cwe:'CWE-79',severity:'high',label:'MALICIOUS',kind:'security'});
    expect(findingGroup(domXss)).toBe('dangerous');
    expect(findingGroup(finding({kind:'lexical'}))).toBe('lexical');expect(findingGroup(finding({kind:'syntax'}))).toBe('syntax');expect(findingGroup(finding({rule_id:'APS-ALL-UNI-006',severity:'low'}))).toBe('suspicious');expect(findingGroup(finding({rule_id:'APS-ALL-ML-001',sources:['ml']}))).toBe('suspicious');
    expect(findingGroup(finding({attack:['T1059']}))).toBe('dangerous');
    expect(findingGroup(finding({evidence:{tags:['malicious']}}))).toBe('malicious');
  });
  it('marks only the js-i09 DOM XSS anchor lexeme insecure',()=>{
    const tokens=[token('element','IDENT',3,49),token('.','PUNCTUATION',3,56),token('innerHTML','IDENT',3,57),token('=','OPERATOR',3,67),token('event','IDENT',3,69),token('.','PUNCTUATION',3,74),token('data','IDENT',3,75),token(';','PUNCTUATION',3,79)];
    const xss=finding({rule_id:'APS-JS-XSS-001',title:'DOM XSS',cwe:'CWE-79',severity:'high',range:{start_line:3,start_col:49,end_line:3,end_col:79},evidence:{sink:'element.innerHTML = event.data'}});
    const rows=adaptTokens({tokens,findings:[xss]} as any);
    expect(rows.find((row)=>row.lexeme==='element.innerHTML')?.security).toBe('insecure');
    expect(rows.filter((row)=>row.lexeme!=='element.innerHTML').every((row)=>row.security==='safe')).toBe(true);
  });
  it('builds labels, sources, explanations and confidence only from returned fields',()=>{const f=finding();expect(typeLabel(f)).toBe('OS command injection');expect(foundBy(f)).toBe('token rule + taint path');expect(confidenceText(f)).toContain('0.7 x rule 0.80 + 0.3 x ML 0.88');expect(explanationText({lexical:'valid',security:'insecure'} as any,f)).toContain('Not a lexical error');expect(typeLabel(finding({kind:'syntax'}))).toBe('Syntax error');expect(confidenceText(finding({evidence:{},confidence:.5}))).toBe('Confidence 0.50');});
  it('shows invisible controls and renders analyzed markup as literal text',()=>{expect(visibleText('\u202E')).toBe('<U+202E>');const markup=renderToStaticMarkup(React.createElement('code',null,visibleText('<img onerror=alert(1)>')));expect(markup).toContain('&lt;img');expect(markup).not.toContain('<img');});
});

const rgb=(hex:string)=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);
const lum=(hex:string)=>{const [r,g,b]=rgb(hex);return .2126*r+.7152*g+.0722*b;};
const ratio=(fg:string,bg:string)=>{const a=lum(fg),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);};
describe('UI-5 contrast tokens',()=>{it.each([['#F0EFEC','#1A1A19'],['#C3C2B7','#1A1A19'],['#898781','#1A1A19'],['#6DA7EC','#151515'],['#0CA30C','#11260F'],['#DB9300','#311A00'],['#EC7E7E','#3C0E0E']])('%s on %s meets 4.5:1', (fg,bg)=>expect(ratio(fg,bg)).toBeGreaterThanOrEqual(4.5));});
