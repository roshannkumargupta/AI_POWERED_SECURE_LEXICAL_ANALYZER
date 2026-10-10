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
