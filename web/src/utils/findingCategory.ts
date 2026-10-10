import { Finding } from '../api/client';

const cweCategories: Record<string, string> = {
  '78': 'Command Injection',
  '89': 'SQL Injection',
  '79': 'XSS',
  '95': 'Code Injection',
  '94': 'Code Injection',
  '502': 'Unsafe Deserialization',
  '327': 'Weak Crypto',
  '798': 'Hard-coded Secret',
  '22': 'Path Traversal',
  '120': 'Memory Safety',
  '787': 'Memory Safety',
  '134': 'Memory Safety',
  '611': 'XXE',
  '918': 'Network Security',
  '295': 'Network Security',
  '506': 'Unicode Security',
  '1007': 'Unicode Security',
  '116': 'Unicode Security',
};

export function findingCategory(finding: Pick<Finding, 'cwe' | 'rule_id'>): string {
  const match = String(finding.cwe || '').match(/\d+/)?.[0];
  if (match && cweCategories[match]) return cweCategories[match];
  const code = String(finding.rule_id || '').split(/[-_:]/)[0];
  return code || 'Other';
}
