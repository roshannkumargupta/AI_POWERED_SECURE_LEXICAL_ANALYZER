import type { AnalysisResult, Finding, TokenInfo } from '../api/client';

export type TokenType = 'KEYWORD'|'IDENT'|'CALL'|'STRING'|'NUMBER'|'OPERATOR'|'DELIM'|'COMMENT'|'ERROR'|'OTHER';
export type TokenGroup = 'safe'|'dangerous'|'suspicious'|'malicious'|'lexical'|'syntax';
export type TokenRow = { id:string; line:number; col:number; endLine:number; endCol:number; lexeme:string; type:TokenType; lexical:'valid'|'error'; security:'safe'|'insecure'|'na'; group:TokenGroup; findingIds:string[]; primaryFindingId:string|null; rawTokenIds:string[] };

const kindType: Record<string,TokenType> = {
  KEYWORD:'KEYWORD', IDENTIFIER:'IDENT', IDENT:'IDENT', NAME:'IDENT', FUNCTION:'IDENT',
  CALL:'CALL', STRING:'STRING', NUMBER:'NUMBER', INTEGER:'NUMBER', FLOAT:'NUMBER',
  OPERATOR:'OPERATOR', PUNCTUATION:'DELIM', DELIMITER:'DELIM', WHITESPACE:'OTHER',
  NEWLINE:'OTHER', INDENT:'OTHER', DEDENT:'OTHER', COMMENT:'COMMENT', ERROR:'ERROR',
  CHAR:'STRING', CHARACTER:'STRING', PREPROCESSOR:'OTHER',
};
const sev = ['critical','high','medium','low','info'];
export function mapTokenType(kind?: string): TokenType { return kindType[(kind || '').toUpperCase()] || 'OTHER'; }
function rangesOverlap(a:any,b:any):boolean { return !!a&&!!b&&((a.start_line < b.end_line || a.start_line===b.end_line&&a.start_col<b.end_col)&&(b.start_line<a.end_line||b.start_line===a.end_line&&b.start_col<a.end_col)); }
function anchorsRow(row: TokenRow, finding: Finding): boolean {
  const range = finding.range;
  return row.line === range.start_line && row.col <= range.start_col && range.start_col < row.endCol;
}
export function findingGroup(f?:Finding):TokenGroup {
  if (!f) return 'safe';
  if (f.kind==='lexical') return 'lexical'; if(f.kind==='syntax') return 'syntax';
  if (Array.isArray(f.evidence?.tags) && f.evidence.tags.some((tag: unknown) => String(tag).toLowerCase() === 'malicious')) return 'malicious';
  if (f.rule_id==='APS-ALL-ML-001' || (f.sources?.includes('ml') && !f.sources.some((source) => source === 'rule' || source === 'taint'))) return 'suspicious';
  if (['critical','high'].includes(f.severity) && (f.sources?.some((source) => source === 'rule' || source === 'taint') || Boolean(f.taint_path?.length))) return 'dangerous';
  if (f.rule_id.startsWith('APS-ALL-UNI-')) return 'suspicious';
  return 'suspicious';
}
export function mergeLexemes(input:TokenInfo[]):TokenRow[] {
  const tokens=input.map((t,i)=>({t,i,kind:(t.token_type||'').toUpperCase(),text:String(t.token??t.text??'')}))
    .filter(x=>!['WHITESPACE','NEWLINE','INDENT','DEDENT'].includes(x.kind)&&x.text.trim()!=='');
  const out:TokenRow[]=[];
  for(let p=0;p<tokens.length;p++){
    let x=tokens[p], parts=[x], end=p;
    if(mapTokenType(x.kind)==='IDENT'){
      while(end+2<tokens.length&&['.','::'].includes(tokens[end+1].text)&&mapTokenType(tokens[end+2].kind)==='IDENT') {parts.push(tokens[end+1],tokens[end+2]);end+=2;}
      if(end>p&&tokens[end+1]?.text==='(') p=end-1;
    }
    const first=parts[0],last=parts.at(-1)!;
    const lexeme=parts.map(a=>a.text).join('');
    const type=end>p&&tokens[end+1]?.text==='('? 'CALL':mapTokenType(first.kind);
    out.push({id:`token-${first.i}`,line:first.t.range?.start_line??first.t.line??1,col:first.t.range?.start_col??first.t.col??1,endLine:last.t.range?.end_line??last.t.line??1,endCol:last.t.range?.end_col??(last.t.col??1)+last.text.length,lexeme,type,lexical:type==='ERROR'?'error':'valid',security:type==='ERROR'?'na':'safe',group:type==='ERROR'?'lexical':'safe',findingIds:[],primaryFindingId:null,rawTokenIds:parts.map(a=>`token-${a.i}`)});
    p=end;
  }
  return out;
}
export function adaptTokens(result?:Partial<AnalysisResult>|null):TokenRow[] {
  if(!result)return [];
  const findings=result.findings||[]; const rows=mergeLexemes(result.tokens||[]);
  for(const row of rows){
    const range={start_line:row.line,start_col:row.col,end_line:row.endLine,end_col:row.endCol};
    const overlapping=findings.filter(f=>rangesOverlap(range,f.range));
    const lexical= row.type==='ERROR'||overlapping.some(f=>f.kind==='lexical');
    const related=overlapping.filter(f=>f.kind==='lexical'||anchorsRow(row,f));
    const primary=related.sort((a,b)=>sev.indexOf(a.severity)-sev.indexOf(b.severity))[0];
    row.findingIds=related.map(f=>f.id);row.primaryFindingId=primary?.id??null;
    row.lexical=lexical?'error':'valid';row.security=lexical?'na':primary?'insecure':'safe';row.group=lexical?'lexical':findingGroup(primary);
  }
  return rows;
}
const cweNames:Record<string,string>={'CWE-78':'OS command injection','CWE-89':'SQL injection','CWE-79':'Cross-site scripting','CWE-95':'Code injection','CWE-94':'Code injection','CWE-502':'Unsafe deserialization','CWE-327':'Weak cryptography','CWE-798':'Hardcoded credentials','CWE-295':'Certificate validation','CWE-22':'Path traversal','CWE-120':'Buffer overflow','CWE-787':'Buffer overflow','CWE-134':'Format string','CWE-611':'XML external entity','CWE-918':'Server-side request forgery','CWE-1007':'Unicode confusable or hidden characters','CWE-176':'Unicode confusable or hidden characters','CWE-116':'Unicode confusable or hidden characters'};
export function typeLabel(f?:Finding|null):string {if(!f)return '';if(f.kind==='lexical')return 'Lexical error';if(f.kind==='syntax')return 'Syntax error';return cweNames[f.cwe]||f.title||'Security finding';}
export function foundBy(f?:Finding|null):string {return (f?.sources||[]).map(s=>({rule:'token rule',taint:'taint path',ml:'ML model',unicode:'Unicode defence',lexical:'lexer',syntax:'parser'} as Record<string,string>)[s]||s).join(' + ');}
export function confidenceText(f?:Finding|null):string {if(!f)return '';const b=f.evidence?.confidence_breakdown;if(!b)return `Confidence ${Number(f.confidence??0).toFixed(2)}`;const fused=Number(b.fused??f.confidence??0).toFixed(2);if(b.rule_weight===1&&b.ml_mode==='off')return `Rule ${Number(b.rule_score??0).toFixed(2)} (ML off)${b.taint_confirmed?`, plus ${Number(b.taint_bonus??0).toFixed(2)} taint confirmed = ${fused}`:''}`;return `${Number(b.rule_weight??0).toFixed(1)} x rule ${Number(b.rule_score??0).toFixed(2)} + ${Number(b.ml_weight??0).toFixed(1)} x ML ${Number(b.ml_score??0).toFixed(2)} = ${Number(b.rule_weight??0)*Number(b.rule_score??0)+Number(b.ml_weight??0)*Number(b.ml_score??0) ? (Number(b.rule_weight??0)*Number(b.rule_score??0)+Number(b.ml_weight??0)*Number(b.ml_score??0)).toFixed(2):'0.00'}${b.taint_confirmed?`, plus ${Number(b.taint_bonus??0).toFixed(2)} taint confirmed = ${fused}`:''}`;}
export function explanationText(row?:TokenRow|null,f?:Finding|null):string {if(row?.lexical==='error')return f?.message||'Lexical error.';if(row?.security==='insecure')return `Not a lexical error, but it is not secure code. ${f?.explanation||f?.message||''}`;return 'Valid token. Nothing to report.';}
export function visibleText(text:string):string {return Array.from(text).map(ch=>{const cp=ch.codePointAt(0)!;return cp<32||cp===127||(cp>=0x200b&&cp<=0x200f)||(cp>=0x202a&&cp<=0x202e)||(cp>=0x2060&&cp<=0x206f)||(cp>=0xfe00&&cp<=0xfe0f)?`<U+${cp.toString(16).toUpperCase().padStart(4,'0')}>`:ch;}).join('');}
