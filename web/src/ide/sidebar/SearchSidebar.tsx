import { useMemo, useState } from 'react';
import type { IDEDocument } from '../state/store';
import type { Range } from '../../utils/offsets';

interface Props { documents: IDEDocument[]; onOpen(doc: IDEDocument, range: Range): void }
export function SearchSidebar({ documents, onOpen }: Props) {
  const [query, setQuery] = useState('');
  const matches = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    if (!needle) return [];
    return documents.flatMap(doc => {
      const lines = doc.source.split(/\r?\n/);
      const found: Array<{ doc: IDEDocument; line: string; lineNumber: number; start: number; end: number }> = [];
      lines.forEach((line, index) => { let cursor = 0; const haystack = line.toLocaleLowerCase(); while ((cursor = haystack.indexOf(needle, cursor)) >= 0) { found.push({ doc, line, lineNumber: index + 1, start: cursor + 1, end: cursor + needle.length + 1 }); cursor += Math.max(needle.length, 1); } });
      return found;
    });
  }, [documents, query]);
  return <div className="ide-sidebar-scroll ide-search-sidebar"><label className="ide-sidebar-search"><span className="material-symbols-outlined" aria-hidden="true">search</span><input aria-label="Search open documents" placeholder="Search open files" value={query} onChange={event => setQuery(event.target.value)} /></label>{!query.trim() ? <p className="ide-tree-message">Search text across {documents.length} open document{documents.length === 1 ? '' : 's'}.</p> : matches.length ? matches.map((match, index) => <button type="button" className="ide-search-match" key={`${match.doc.id}-${match.lineNumber}-${match.start}-${index}`} onClick={() => onOpen(match.doc, { start_line: match.lineNumber, start_col: match.start, end_line: match.lineNumber, end_col: match.end })}><strong>{match.doc.name}:{match.lineNumber}:{match.start}</strong><code>{match.line.trim()}</code></button>) : <p className="ide-tree-message">No matches in open documents.</p>}</div>;
}
