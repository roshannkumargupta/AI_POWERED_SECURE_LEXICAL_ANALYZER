import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Finding, SampleItem, AnalysisResult } from '../api/client';
import { compareSample, DEMO_PATH } from '../utils/sampleDemo';

interface FindingDemoBarProps {
  sample: SampleItem;
  sampleEdited?: boolean;
  onDemoStep?: (delta: number) => void;
  findings?: Finding[];
  analysis?: AnalysisResult | null;
}

export const FindingDemoBar: React.FC<FindingDemoBarProps> = ({
  sample,
  sampleEdited = false,
  onDemoStep,
  findings = [],
  analysis = null,
}) => {
  return (
    <>
      {sample.demo_order && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 6,
            padding: '6px 12px 0',
          }}
        >
          <button disabled={DEMO_PATH.indexOf(sample.id) <= 0} onClick={() => onDemoStep?.(-1)}>
            Previous
          </button>
          <button
            disabled={DEMO_PATH.indexOf(sample.id) >= DEMO_PATH.length - 1}
            onClick={() => onDemoStep?.(1)}
          >
            Next
          </button>
        </div>
      )}
      <details style={{ margin: '8px 12px', color: 'var(--muted)', fontSize: 11 }}>
        <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>Demo notes</summary>
        <div style={{ display: 'grid', gap: 6, padding: '8px 0' }}>
          <div>{sample.summary || sample.description}</div>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {(sample.notes || []).slice(0, 4).map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
          <div>
            Expected: {(sample.expect?.findings || []).length} findings -{' '}
            {(sample.expect?.findings || []).map((item) => item.rule_id).join(', ') || 'none'}
          </div>
          {analysis && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: sampleEdited
                  ? 'var(--amber)'
                  : compareSample(sample, findings, false) === 'Matches expected'
                    ? 'var(--success)'
                    : 'var(--amber)',
              }}
            >
              {!sampleEdited && compareSample(sample, findings, false) === 'Matches expected' && (
                <CheckCircle2 size={12} />
              )}
              {sampleEdited ? 'Edited - comparison paused' : compareSample(sample, findings, false)}
            </div>
          )}
          {sample.senior && (
            <div>
              Senior project:{' '}
              {sample.senior.flagged === null
                ? sample.senior.detail
                : sample.senior.flagged
                  ? `flagged ${sample.senior.detail}`
                  : 'not flagged'}{' '}
              <small>
                senior tool run without its ML model
                {sample.senior.note ? ` · ${sample.senior.note}` : ''}
              </small>
            </div>
          )}
        </div>
      </details>
    </>
  );
};
