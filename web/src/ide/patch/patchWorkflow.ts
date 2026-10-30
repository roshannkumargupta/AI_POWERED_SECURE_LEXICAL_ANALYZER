import type { PatchProposal } from '../../api/client';
import { rangeToOffsets, type Range } from '../../utils/offsets';
import { applyEdits } from '../../utils/applyEdits';
import { generateUnifiedDiff } from '../../utils/diff';

export interface PatchValidationResult {
  valid: boolean;
  reason?: string;
  conflictType?: 'stale_version' | 'content_mismatch' | 'invalid_range' | 'overlapping_edits';
}

export interface EnrichedPatchProposal extends PatchProposal {
  target_file: string;
  original_text: string;
  replacement_text: string;
  original_range: Range;
  finding?: {
    id: string;
    title: string;
    rule_id?: string;
    severity?: string;
  };
  explanation: string;
}

/**
 * Validates whether a proposed patch can be cleanly applied to current source.
 * Enforces:
 * 1. Document version must match proposal source_version.
 * 2. Target source range must strictly match original expected text.
 * 3. Range coordinates must be valid within document bounds.
 */
export function validatePatchProposal(
  currentSource: string,
  currentVersion: number,
  proposal: PatchProposal
): PatchValidationResult {
  // 1. Version check
  if (currentVersion !== proposal.source_version) {
    return {
      valid: false,
      reason: `Stale patch rejected: Document is currently v${currentVersion}, but proposal was generated for v${proposal.source_version}.`,
      conflictType: 'stale_version',
    };
  }

  // 2. Target range content check
  const originalText = (proposal as Partial<EnrichedPatchProposal>).original_text;
  const originalRange = (proposal as Partial<EnrichedPatchProposal>).original_range;

  if (originalText !== undefined && originalRange !== undefined) {
    const { startOffset, endOffset } = rangeToOffsets(currentSource, originalRange);
    const actualText = currentSource.slice(startOffset, endOffset);
    if (actualText !== originalText) {
      return {
        valid: false,
        reason: `Content conflict rejected: Expected '${originalText}' at [Ln ${originalRange.start_line}:${originalRange.start_col}], but found '${actualText}'.`,
        conflictType: 'content_mismatch',
      };
    }
  }

  // 3. Verify each edit's range within document
  for (const edit of proposal.edits) {
    const { startOffset, endOffset } = rangeToOffsets(currentSource, edit.range);
    if (startOffset > currentSource.length || endOffset > currentSource.length) {
      return {
        valid: false,
        reason: `Invalid range rejected: Edit offset [${startOffset}, ${endOffset}) exceeds document length (${currentSource.length}).`,
        conflictType: 'invalid_range',
      };
    }
  }

  return { valid: true };
}

/**
 * Applies a validated proposal to source text.
 */
export function applyPatchToSource(
  currentSource: string,
  proposal: PatchProposal
): { success: boolean; newSource?: string; error?: string } {
  try {
    const newSource = applyEdits(currentSource, proposal.edits);
    return { success: true, newSource };
  } catch (err: any) {
    return {
      success: false,
      error: err?.message || 'Failed to apply patch edits.',
    };
  }
}

/**
 * Builds an enriched patch proposal containing all required audit metadata:
 * - Target file
 * - Original source version & hash
 * - Original source range
 * - Original text
 * - Replacement text
 * - Explanation
 * - Related finding
 */
export function createEnrichedPatchProposal(
  baseProposal: PatchProposal,
  source: string,
  fileName: string,
  finding?: { id: string; title: string; rule_id?: string; severity?: string }
): EnrichedPatchProposal {
  const firstEdit = baseProposal.edits[0];
  let originalRange: Range = {
    start_line: 1,
    start_col: 1,
    end_line: 1,
    end_col: 1,
  };
  let originalText = '';
  let replacementText = '';

  if (firstEdit) {
    originalRange = firstEdit.range;
    const { startOffset, endOffset } = rangeToOffsets(source, originalRange);
    originalText = source.slice(startOffset, endOffset);
    replacementText = baseProposal.edits.map((e) => e.new_text).join('\n');
  }

  return {
    ...baseProposal,
    target_file: fileName,
    original_range: originalRange,
    original_text: originalText,
    replacement_text: replacementText,
    finding,
    explanation: baseProposal.rationale || 'Automated deterministic remediation patch.',
  };
}

/**
 * Intelligently extracts a proposed patch from an AI response (text / code blocks)
 * comparing against the active document source.
 */
export function extractProposedPatchFromAiResponse(
  activeDoc: { name: string; source: string; sourceVersion: number; sourceHash?: string; language?: string },
  aiReply: string,
  codeSnippets?: string[]
): { proposal: EnrichedPatchProposal; diff: { file: string; unifiedDiff: string } } | null {
  if (!activeDoc || !activeDoc.source) return null;

  // 1. Gather all candidate code blocks from aiReply and codeSnippets
  const candidateBlocks: string[] = [];

  if (codeSnippets && codeSnippets.length > 0) {
    for (const snip of codeSnippets) {
      if (typeof snip === 'string' && snip.trim()) {
        candidateBlocks.push(snip.trim());
      }
    }
  }

  const codeFenceRegex = /```(?:[a-zA-Z0-9_\-+]*)\s*\n([\s\S]*?)```/g;
  let match: RegExpExecArray | null;
  while ((match = codeFenceRegex.exec(aiReply)) !== null) {
    const block = match[1].trim();
    if (block && !candidateBlocks.includes(block)) {
      candidateBlocks.push(block);
    }
  }

  if (candidateBlocks.length === 0) return null;

  const currentSource = activeDoc.source;
  const oldLines = currentSource.split('\n');

  // Find the candidate block that represents a valid modification of the current file
  for (const candidate of candidateBlocks) {
    if (candidate === currentSource.trim()) {
      continue; // No change
    }

    const newLines = candidate.split('\n');

    // Scenario A: Candidate is a full file (or substantial replacement)
    const isLikelyFullFile =
      newLines.length >= Math.max(3, Math.floor(oldLines.length * 0.4)) ||
      candidate.includes('#include') ||
      candidate.includes('int main') ||
      candidate.includes('class ') ||
      candidate.includes('def ') ||
      candidate.includes('import ');

    if (isLikelyFullFile) {
      // Find top mismatch
      let start = 0;
      while (
        start < oldLines.length &&
        start < newLines.length &&
        oldLines[start] === newLines[start]
      ) {
        start++;
      }

      // Find bottom mismatch
      let oldEnd = oldLines.length - 1;
      let newEnd = newLines.length - 1;
      while (
        oldEnd >= start &&
        newEnd >= start &&
        oldLines[oldEnd] === newLines[newEnd]
      ) {
        oldEnd--;
        newEnd--;
      }

      // If there are differences
      if (start <= oldEnd || start <= newEnd) {
        let editRange: Range;
        let originalText: string;
        let replacementText: string;

        if (start <= oldEnd && start <= newEnd) {
          editRange = {
            start_line: start + 1,
            start_col: 1,
            end_line: oldEnd + 1,
            end_col: (oldLines[oldEnd] || '').length + 1,
          };
          originalText = oldLines.slice(start, oldEnd + 1).join('\n');
          replacementText = newLines.slice(start, newEnd + 1).join('\n');
        } else if (start > oldEnd) {
          // Insertion
          const insertLine = Math.min(start + 1, oldLines.length + 1);
          editRange = {
            start_line: insertLine,
            start_col: 1,
            end_line: insertLine,
            end_col: 1,
          };
          originalText = '';
          replacementText = newLines.slice(start, newEnd + 1).join('\n') + '\n';
        } else {
          // Deletion
          editRange = {
            start_line: start + 1,
            start_col: 1,
            end_line: oldEnd + 1,
            end_col: (oldLines[oldEnd] || '').length + 1,
          };
          originalText = oldLines.slice(start, oldEnd + 1).join('\n');
          replacementText = '';
        }

        const unifiedDiff = generateUnifiedDiff(currentSource, candidate, activeDoc.name);

        const baseProposal: PatchProposal = {
          id: `prop-${Date.now()}`,
          source_version: activeDoc.sourceVersion,
          source_hash: activeDoc.sourceHash || '',
          target_finding_id: `ai-fix-${Date.now()}`,
          target_kind: 'finding',
          origin: 'ai',
          diff: unifiedDiff,
          rationale: 'Applied AI suggestion from chat response.',
          expected_outcome: 'Resolves detected compiler/syntax issue',
          assumptions: [],
          risks: [],
          created_at: new Date().toISOString(),
          edits: [
            {
              range: editRange,
              new_text: replacementText,
            },
          ],
        };

        const enriched: EnrichedPatchProposal = {
          ...baseProposal,
          target_file: activeDoc.name,
          original_range: editRange,
          original_text: originalText,
          replacement_text: replacementText,
          finding: {
            id: `ai-fix-${Date.now()}`,
            title: 'AI Proposed Modification',
          },
          explanation: 'AI proposed code fix based on analysis.',
        };

        return {
          proposal: enriched,
          diff: {
            file: activeDoc.name,
            unifiedDiff,
          },
        };
      }
    }

    // Scenario B: Candidate is a snippet that can replace a matching substring in source
    const trimmedCandidate = candidate.trim();
    const candidateBase = trimmedCandidate.replace(/[;\s]+$/, '');
    const matchedLineIndex = oldLines.findIndex(
      (line) =>
        line.trim().length > 0 &&
        (line.trim() === candidateBase ||
          line.trim().replace(/[;\s]+$/, '') === candidateBase)
    );

    if (matchedLineIndex !== -1 && oldLines[matchedLineIndex].trim() !== trimmedCandidate) {
      const origLine = oldLines[matchedLineIndex];
      const indentMatch = origLine.match(/^(\s*)/);
      const indent = indentMatch ? indentMatch[1] : '';
      const fixedLine = `${indent}${trimmedCandidate}`;

      const editRange: Range = {
        start_line: matchedLineIndex + 1,
        start_col: 1,
        end_line: matchedLineIndex + 1,
        end_col: origLine.length + 1,
      };

      const newSourceLines = [...oldLines];
      newSourceLines[matchedLineIndex] = fixedLine;
      const newSource = newSourceLines.join('\n');
      const unifiedDiff = generateUnifiedDiff(currentSource, newSource, activeDoc.name);

      const baseProposal: PatchProposal = {
        id: `prop-${Date.now()}`,
        source_version: activeDoc.sourceVersion,
        source_hash: activeDoc.sourceHash || '',
        target_finding_id: `ai-fix-${Date.now()}`,
        target_kind: 'finding',
        origin: 'ai',
        diff: unifiedDiff,
        rationale: 'Applied AI suggested line replacement.',
        expected_outcome: 'Resolves detected syntax/token issue',
        assumptions: [],
        risks: [],
        created_at: new Date().toISOString(),
        edits: [
          {
            range: editRange,
            new_text: fixedLine,
          },
        ],
      };

      const enriched: EnrichedPatchProposal = {
        ...baseProposal,
        target_file: activeDoc.name,
        original_range: editRange,
        original_text: origLine,
        replacement_text: fixedLine,
        finding: {
          id: `ai-fix-${Date.now()}`,
          title: 'AI Proposed Modification',
        },
        explanation: 'AI proposed replacement for matching line.',
      };

      return {
        proposal: enriched,
        diff: {
          file: activeDoc.name,
          unifiedDiff,
        },
      };
    }
  }

  return null;
}
