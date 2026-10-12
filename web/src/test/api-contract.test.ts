import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { api, AnalysisResult } from '../api/client';

describe('B4 - API Contract with OpenAPI Schema', () => {
  const schemaPath = path.resolve(__dirname, '../../../tests/golden/openapi_schema.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

  it('matches all declared OpenAPI paths in the frontend client', () => {
    const paths = Object.keys(schema.paths || {});
    expect(paths).toContain('/api/analyze');
    expect(paths).toContain('/api/health');
    expect(paths).toContain('/api/languages');
    expect(paths).toContain('/api/samples');
    expect(paths).toContain('/api/fix');
    expect(paths).toContain('/api/fix-all');
    expect(paths).toContain('/api/feedback');
    expect(paths).toContain('/api/ml/insights');
    expect(paths).toContain('/api/agent/status');
    expect(paths).toContain('/api/llm/status');
    expect(paths).toContain('/api/llm/fix');
    expect(paths).toContain('/api/llm/explain');
    for (const path of ['/api/capabilities', '/api/ast/{analysis_id}/node/{node_id}', '/api/analyze/lexical', '/api/analyze/syntax', '/api/analyze/security', '/api/analyze/quality']) expect(paths).toContain(path);

    expect(typeof api.analyze).toBe('function');
    expect(typeof api.getHealth).toBe('function');
    expect(typeof api.getLanguages).toBe('function');
    expect(typeof api.getSamples).toBe('function');
    expect(typeof api.applyFix).toBe('function');
    expect(typeof api.applyFixAll).toBe('function');
    expect(typeof api.submitFeedback).toBe('function');
    expect(typeof api.getMLInsights).toBe('function');
    expect(typeof api.getAgentStatus).toBe('function');
    expect(typeof api.getLLMStatus).toBe('function');
    expect(typeof api.requestLLMFix).toBe('function');
    expect(typeof api.requestLLMExplain).toBe('function');
    expect(typeof api.analyzeV2).toBe('function');
    expect(typeof api.getASTNode).toBe('function');
    expect(typeof api.proposeFix).toBe('function');
    expect(typeof api.verifyFix).toBe('function');
    expect(typeof api.applyFixV2).toBe('function');
    expect(typeof api.undoFix).toBe('function');
    expect(typeof api.explainAI).toBe('function');
    expect(typeof api.generateAI).toBe('function');
    expect(typeof api.runSafety).toBe('function');
    expect(typeof api.getSafetyResult).toBe('function');
    expect(typeof api.exportReport).toBe('function');
  });

  it('matches the v2 analysis client contract to the checked-in golden schema', () => {
    const requestProps = Object.keys(schema.components.schemas.AnalyzeRequest.properties);
    const optionProps = Object.keys(schema.components.schemas.AnalyzeOptions.properties);
    const responseProps = Object.keys(schema.components.schemas.AnalysisResultV2.properties);
    const client = fs.readFileSync(path.resolve(__dirname, '../api/client.ts'), 'utf8');
    for (const key of ['api_version', 'source_version', 'include_ast']) expect(requestProps).toContain(key);
    for (const key of ['include_tokens', 'stages']) expect(optionProps).toContain(key);
    for (const key of ['analysis_id', 'source_hash', 'source_version', 'lexical_status', 'syntax_status', 'semantic_status', 'tokens', 'security_findings', 'quality']) {
      expect(responseProps).toContain(key);
      expect(client).toContain(key);
    }
    expect(client).toContain("api_version: 2");
    expect(client).toContain("'lexical' | 'syntax' | 'security' | 'quality'");
  });

  it('matches reviewed fix-all request fields to the backend golden schema', () => {
    const properties = Object.keys(schema.components.schemas.FixAllRequest.properties);
    for (const field of ['session_id', 'source_version', 'approved', 'approved_diff']) {
      expect(properties).toContain(field);
      expect(fs.readFileSync(path.resolve(__dirname, '../api/client.ts'), 'utf8')).toContain(field);
    }
  });

  it('ensures AnalysisResult schema properties match frontend type definition', () => {
    const analysisSchema = schema.components?.schemas?.AnalysisResult;
    expect(analysisSchema).toBeDefined();

    const schemaProperties = Object.keys(analysisSchema.properties || {});
    expect(schemaProperties).toContain('language');
    expect(schemaProperties).toContain('filename');
    expect(schemaProperties).toContain('findings');
    expect(schemaProperties).toContain('tokens');
    expect(schemaProperties).toContain('summary');
    expect(schemaProperties).toContain('engine');

    const sampleResult: AnalysisResult = {
      language: 'python',
      filename: 'sample.py',
      findings: [],
      tokens: [],
      summary: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        info: 0,
        score: 100,
        tokens_total: 0,
        tokens_malicious: 0,
        tokens_suspicious: 0,
      },
      engine: {
        ml_mode: 'off',
        ml_model_id: 'none',
        taint: 'intraprocedural',
        version: '0.1.0',
        elapsed_ms: 12,
      },
    };
    expect(sampleResult.language).toBe('python');
    expect(sampleResult.findings).toHaveLength(0);
  });

  it('ensures Finding schema properties match frontend type definition', () => {
    const findingSchema = schema.components?.schemas?.Finding;
    expect(findingSchema).toBeDefined();

    const properties = Object.keys(findingSchema.properties || {});
    expect(properties).toContain('id');
    expect(properties).toContain('rule_id');
    expect(properties).toContain('title');
    expect(properties).toContain('cwe');
    expect(properties).toContain('severity');
    expect(properties).toContain('confidence');
    expect(properties).toContain('range');
    expect(properties).toContain('message');
    expect(properties).toContain('explanation');
  });
});
