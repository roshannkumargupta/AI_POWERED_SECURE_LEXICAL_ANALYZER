import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { AnalysisResult, Finding, TokenInfo } from '../api/client';
import { TokensPanel } from '../components/TokensPanel';

const range = (line:number,start:number,end:number) => ({start_line:line,start_col:start,end_line:line,end_col:end});
function finding(id:string, line:number, start:number, end:number, kind:Finding['kind']='security', label:Finding['label']='MALICIOUS'):Finding { return {id,rule_id:`APS-PY-${id}`,title:id,message:`${id} message`,explanation:`${id} explanation`,cwe:'CWE-78',severity:'critical',label,confidence:.9,range:range(line,start,end),evidence:{},taint_path:[],fixes:[],sources:['rule'],kind}; }
function result(tokens:TokenInfo[],findings:Finding[]=[]):AnalysisResult {return {language:'python',filename:'sample.py',tokens,findings,summary:{critical:findings.length,high:0,medium:0,low:0,info:0,score:100,tokens_total:tokens.length,tokens_malicious:0,tokens_suspicious:0},engine:{ml_mode:'off',ml_model_id:'',taint:'ast',version:'',elapsed_ms:1,parser:'python-ast'}};}
const base={language:'python',selectedIndex:null,selectedFindingId:null,mlMode:'off',ml:null,loadingML:false,onSelectToken:vi.fn(),onSelectFinding:vi.fn(),onLoadML:vi.fn(),onTokenMap:vi.fn(),tokenMap:'off' as const,category:'',onCategoryChange:vi.fn(),showAll:false,mainFilter:'All' as const,groups:[] as string[]};

describe('UI-6 token table',()=>{
  it('defaults to security and lexical problem rows and reveals safe rows with Show all tokens',()=>{
    const data=result([{token:'safe_name',token_type:'IDENTIFIER',range:range(1,1,10),label:'SAFE',score:0},{token:'os.system',token_type:'IDENTIFIER',range:range(1,12,21),label:'MALICIOUS',score:.9},{token:'"broken',token_type:'STRING',range:range(2,1,8),label:'SAFE',score:0}],[finding('unsafe',1,12,21),finding('unterminated',2,1,8,'lexical','SUSPICIOUS')]);
    const {container}=render(<TokensPanel {...base} result={data}/>);
    expect(screen.getByText('2 problem rows')).toBeTruthy(); expect(screen.getByText('os.system')).toBeTruthy(); expect(screen.getByText('"broken')).toBeTruthy(); expect(screen.queryByText('safe_name')).toBeNull();
    render(<TokensPanel {...base} result={data} showAll/>); expect(screen.getByText('safe_name')).toBeTruthy();
    expect(container.querySelector('table colgroup')?.textContent).toBe('');
    expect(container.querySelectorAll('colgroup col')).toHaveLength(5);
  });
  it('uses a real accessible table, safe literal rendering, badges, and row selection',()=>{
    const onSelectToken=vi.fn(); const unsafe=finding('img',1,1,28);
    const data=result([{token:'<img src=x onerror=alert(1)>',token_type:'IDENTIFIER',range:range(1,1,28),label:'MALICIOUS',score:.9}],[unsafe]);
    const {container}=render(<TokensPanel {...base} onSelectToken={onSelectToken} result={data}/>);
    expect(screen.getByRole('table',{name:'Tokens'})).toBeTruthy(); expect(container.querySelector('img')).toBeNull();
    expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeTruthy(); expect(screen.getByText('insecure')).toBeTruthy();
    fireEvent.click(screen.getByText('<img src=x onerror=alert(1)>')); expect(onSelectToken).toHaveBeenCalledWith(0);
  });
  it('combines single-choice filters with OR multi-select tags',()=>{
    const rows:TokenInfo[]=[{token:'danger',token_type:'IDENTIFIER',range:range(1,1,7),label:'MALICIOUS',score:.9},{token:'suspect',token_type:'IDENTIFIER',range:range(2,1,8),label:'SUSPICIOUS',score:.7}];
    const data=result(rows,[finding('danger',1,1,7),{...finding('suspect',2,1,8,'security','SUSPICIOUS'),severity:'medium'}]);
    const {rerender}=render(<TokensPanel {...base} result={data} mainFilter="Security" groups={['dangerous','suspicious']}/>);
    expect(screen.getByText('danger')).toBeTruthy(); expect(screen.getByText('suspect')).toBeTruthy();
    rerender(<TokensPanel {...base} result={data} mainFilter="Lexical" groups={['dangerous','suspicious']}/>); expect(screen.getByText('No rows match the filters.')).toBeTruthy();
    rerender(<TokensPanel {...base} result={data} mainFilter="All"/>); expect(screen.getByText('danger')).toBeTruthy();
  });
  it('shows the correct empty states and virtualizes large tables',()=>{
    const empty=result([]); const {rerender,container}=render(<TokensPanel {...base} result={empty}/>); expect(screen.getByText(/No security or lexical problems found/)).toBeTruthy();
    const many=result(Array.from({length:250},(_,i)=>({token:`name${i}`,token_type:'IDENTIFIER',range:range(i+1,1,7),label:'SAFE',score:0})));
    rerender(<TokensPanel {...base} result={many} showAll/>);
    expect(container.querySelectorAll('tbody tr:not(.ui6-spacer)')).toHaveLength(200);
  });
});
