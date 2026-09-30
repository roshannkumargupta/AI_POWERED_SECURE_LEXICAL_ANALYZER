import { describe, it, expect } from 'vitest';
import {
  severityToMarkerSeverity,
  findingToMarker,
  MARKER_SOURCE,
} from '../monaco/markers';
import { Finding } from '../api/client';

// Mock Monaco instance
const mockMonaco: any = {
  MarkerSeverity: {
    Hint: 1,
    Info: 2,
    Warning: 4,
    Error: 8,
  },
};

describe('Monaco Markers Mapping', () => {
  it('maps severity levels to correct Monaco MarkerSeverity', () => {
    expect(severityToMarkerSeverity('critical', mockMonaco)).toBe(mockMonaco.MarkerSeverity.Error);
    expect(severityToMarkerSeverity('high', mockMonaco)).toBe(mockMonaco.MarkerSeverity.Error);
    expect(severityToMarkerSeverity('medium', mockMonaco)).toBe(mockMonaco.MarkerSeverity.Warning);
    expect(severityToMarkerSeverity('low', mockMonaco)).toBe(mockMonaco.MarkerSeverity.Info);
    expect(severityToMarkerSeverity('info', mockMonaco)).toBe(mockMonaco.MarkerSeverity.Hint);
  });

  it('converts Finding model to IMarkerData correctly', () => {
    const finding: Finding = {
      id: 'finding-001',
      rule_id: 'APS-PY-INJ-001',
      title: 'Command Injection',
      cwe: 'CWE-78',
      severity: 'critical',
      label: 'MALICIOUS',
      confidence: 0.95,
      range: {
        start_line: 22,
        start_col: 5,
        end_line: 22,
        end_col: 36,
      },
      message: 'Untrusted input reaches os.system shell sink',
      explanation: 'Detailed explanation.',
      evidence: {},
      taint_path: [],
      fixes: [],
      sources: ['rule', 'taint'],
    };

    const marker = findingToMarker(finding, mockMonaco);
    expect(marker.source).toBe(MARKER_SOURCE);
    expect(marker.code).toBe('APS-PY-INJ-001');
    expect(marker.severity).toBe(mockMonaco.MarkerSeverity.Error);
    expect(marker.startLineNumber).toBe(22);
    expect(marker.startColumn).toBe(5);
    expect(marker.endLineNumber).toBe(22);
    expect(marker.endColumn).toBe(36);
    expect(marker.message).toContain('Command Injection');
  });
});
