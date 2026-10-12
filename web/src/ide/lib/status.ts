import type { AnalysisResultV2, CapabilitiesResponse, HealthResponse } from '../../api/client';
import type { IDEDocument } from '../state/store';

export function activeLanguage(doc: IDEDocument | null, capabilities: CapabilitiesResponse | null) {
  return capabilities?.languages.find((language) => language.id === doc?.language) ?? null;
}

export function displayEol(source: string): 'CRLF' | 'LF' {
  return source.includes('\r\n') ? 'CRLF' : 'LF';
}

export function dimensionLabel(result: AnalysisResultV2 | null, dimension: 'lexical' | 'syntax') {
  if (!result) return 'Not analysed';
  const item = dimension === 'lexical' ? result.lexical_status : result.syntax_status;
  if (item.status === 'unavailable') return 'Check unavailable';
  if (item.status === 'incomplete') return 'Analysis incomplete';
  return item.status === 'issues' ? 'Finding detected' : 'No issues detected';
}

export function securityLabel(result: AnalysisResultV2 | null) {
  if (!result) return 'Not analysed';
  if (result.omissions.length && result.tools.every((tool) => tool.status === 'unavailable')) return 'Check unavailable';
  return result.security_findings.length ? `${result.security_findings.length} findings` : 'No findings detected by checks run';
}

export function engineLabel(health: HealthResponse | null, error: boolean) {
  if (health) return health.status;
  return error ? 'Engine unavailable' : 'Loading';
}

export function grammarLabel(doc: IDEDocument | null, capabilities: CapabilitiesResponse | null) {
  const language = activeLanguage(doc, capabilities);
  if (!language) return 'Grammar unavailable';
  const parserName = typeof language.parser.name === 'string' ? language.parser.name : null;
  const lexerName = typeof language.lexer.name === 'string' ? language.lexer.name : null;
  return parserName ?? lexerName ?? 'Grammar unavailable';
}
