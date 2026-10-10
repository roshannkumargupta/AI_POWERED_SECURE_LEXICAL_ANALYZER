import { AnalysisResult } from '../api/client';

export interface DocItem {
  id: string;
  name: string;
  content: string;
  language: string;
  dirty: boolean;
  sampleId?: string;
  folderPath?: string;
  hasCrlf?: boolean;
  analysis: AnalysisResult | null;
  resultVersion: number;
  contentVersion: number;
  status: 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error';
  durationMs?: number;
  errorMessage?: string;
}
