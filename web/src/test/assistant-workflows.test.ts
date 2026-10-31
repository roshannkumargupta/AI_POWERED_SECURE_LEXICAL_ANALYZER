import { describe, it, expect, vi } from 'vitest';
import { apiClient } from '../api/client';
import { applyPatchToSource, validatePatchProposal } from '../ide/patch/patchWorkflow';

describe('SecureLex Assistant & AI Coding Workflows', () => {
  it('includes complete user context in chat queries', async () => {
    const chatSpy = vi.spyOn(apiClient, 'chatAI').mockResolvedValueOnce({
      operation_id: 'op-123',
      reply: 'Detailed compiler assistance.',
      code_snippets: ['int main() { return 0; }'],
      provider: 'groq',
      model: 'openai/gpt-oss-120b',
    });

    const context = {
      file: 'src/main.cpp',
      language: 'cpp',
      source_version: 2,
      selected_range: { start_line: 6, start_col: 10, end_line: 6, end_col: 25 },
      selected_code: 'for (int i = 0; i <= n; i++)',
      selected_token: { id: 24, lexeme: '<=', type: 'OPERATOR', status: 'valid' },
      stage: 'Lexical Scanner',
      finding: { id: 'sec-1', title: 'Trojan Source Bidi Override', line: 6, col: 20 },
      findings_count: 1,
    };

    const res = await apiClient.chatAI({
      session_id: 'test-session-id-12345678',
      message: 'Analyze this loop boundary',
      source: 'int main() { int n = 5; for (int i = 0; i <= n; i++) {} }',
      language: 'cpp',
      history: [{ role: 'user', content: 'Hello' }],
      context,
      remote_consent: true,
    });

    expect(chatSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Analyze this loop boundary',
        language: 'cpp',
        context: expect.objectContaining({
          file: 'src/main.cpp',
          source_version: 2,
          selected_code: 'for (int i = 0; i <= n; i++)',
          selected_token: expect.objectContaining({ id: 24, lexeme: '<=' }),
          stage: 'Lexical Scanner',
        }),
      })
    );

    expect(res.reply).toBe('Detailed compiler assistance.');
    expect(res.code_snippets).toContain('int main() { return 0; }');
  });

  it('validates and applies an AI patch proposal without replacing source on rejection', () => {
    const originalSource = 'int main() {\n    int a = 10;\n    return a;\n}\n';
    const proposal = {
      id: 'prop-1',
      proposal_id: 'prop-1',
      target_finding_id: 'find-1',
      target_kind: 'finding' as const,
      target_signature: 'signature-1',
      source_version: 1,
      source_hash: 'abc123hash',
      diff: '--- a/src/main.cpp\n+++ b/src/main.cpp\n@@ -2,1 +2,1 @@\n-    int a = 10;\n+    const int a = 10;',
      created_at: new Date().toISOString(),
      origin: 'ai' as const,
      rationale: 'Add const qualifier for immutability.',
      expected_outcome: 'Safe immutable variable',
      assumptions: [],
      risks: [],
      edits: [
        {
          range: { start_line: 2, start_col: 5, end_line: 2, end_col: 15 },
          new_text: 'const int a = 10;',
        },
      ],
    };

    // 1. Validation succeeds on matching source version
    const validation = validatePatchProposal(originalSource, 1, proposal);
    expect(validation.valid).toBe(true);

    // 2. Applying patch modifies source as expected
    const applied = applyPatchToSource(originalSource, proposal);
    expect(applied.success).toBe(true);
    expect(applied.newSource).toContain('const int a = 10;');

    // 3. Stale source version rejection prevents out-of-sync corruption
    const staleValidation = validatePatchProposal(originalSource, 2, proposal);
    expect(staleValidation.valid).toBe(false);
    expect(staleValidation.reason).toContain('Stale patch rejected');
  });

  it('supports Build with AI across C++, Python, Java, and JavaScript', async () => {
    const generateSpy = vi.spyOn(apiClient, 'generateAI').mockImplementation(async (req) => ({
      operation_id: 'gen-op-1',
      code: `// Generated ${req.language}\nvoid execute() {}`,
      language: req.language,
      explanation: `Synthesized implementation for ${req.language}.`,
      assumptions: ['Standard library available'],
      requirements_checklist: [
        { requirement: req.requirements[0], status: 'met', evidence: 'Implemented in execute()' },
      ],
      limitations: [],
      analysis: {
        tokens: [],
        security_findings: [],
        syntax_diagnostics: [],
        semantic_diagnostics: [],
      } as any,
      provider: 'groq',
      processing_location: 'remote',
      executed: false,
    } as unknown as any));

    const languages = ['cpp', 'python', 'java', 'javascript'] as const;
    for (const lang of languages) {
      const res = await apiClient.generateAI({
        session_id: 'test-session-id-12345678',
        language: lang,
        requirements: ['Implement a robust tokenizer'],
        remote_consent: true,
      });

      expect(res.language).toBe(lang);
      expect(res.code).toContain(`Generated ${lang}`);
      expect(res.requirements_checklist[0].status).toBe('met');
    }

    expect(generateSpy).toHaveBeenCalledTimes(4);
  });

  it('surfaces actual provider error when remote AI service fails', async () => {
    vi.spyOn(apiClient, 'chatAI').mockRejectedValueOnce(
      new Error('AI service error: Groq API key is invalid or unauthorized.')
    );

    await expect(
      apiClient.chatAI({
        session_id: 'test-session-id-12345678',
        message: 'Test failure path',
        source: '',
        language: 'cpp',
        remote_consent: true,
      })
    ).rejects.toThrow('Groq API key is invalid or unauthorized');
  });
});
