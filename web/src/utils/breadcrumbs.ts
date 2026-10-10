export interface BreadcrumbSegment { label: string; line: number; col: number }

// Best-effort function/class locator. It intentionally degrades to no segment.
export function findEnclosingSymbol(source: string, language: string, targetLine: number): BreadcrumbSegment | null {
  const lang = language.toLowerCase();
  const lines = source.split(/\r?\n/);
  const target = Math.max(1, targetLine);
  let candidate: BreadcrumbSegment | null = null;
  let braceDepth = 0;
  let blocks: Array<{ depth: number; segment: BreadcrumbSegment }> = [];
  for (let i = 0; i < Math.min(target, lines.length); i++) {
    const line = lines[i];
    const trimmed = line.trim();
    let match: RegExpMatchArray | null = null;
    if (lang === 'python') match = trimmed.match(/^(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)/);
    else if (lang === 'javascript' || lang === 'js') match = trimmed.match(/^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)|^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>/);
    else match = trimmed.match(/(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)|(?:[\w<>\[\],.?]+\s+)+([A-Za-z_$][\w$]*)\s*\([^;]*\)\s*(?:throws[^{}]+)?\s*\{/);
    if (match) {
      const label = match[1] || match[2];
      if (lang === 'python') {
        const indent = line.length - line.trimStart().length;
        while (blocks.length && blocks[blocks.length - 1].depth >= indent) blocks.pop();
        const segment = { label, line: i + 1, col: line.indexOf(label) + 1 };
        blocks.push({ depth: indent, segment }); candidate = segment;
      } else {
        const segment = { label, line: i + 1, col: line.indexOf(label) + 1 };
        blocks.push({ depth: braceDepth, segment }); candidate = segment;
      }
    }
    braceDepth += (line.match(/{/g) || []).length - (line.match(/}/g) || []).length;
    if (lang !== 'python') {
      while (blocks.length && braceDepth < blocks[blocks.length - 1].depth) blocks.pop();
      candidate = blocks[blocks.length - 1]?.segment || null;
    }
  }
  return candidate;
}
