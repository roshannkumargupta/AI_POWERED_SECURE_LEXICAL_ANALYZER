import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../../api/client';
import { ASTSidebar } from './ASTSidebar';

vi.mock('../../api/client', () => ({ apiClient: { getASTNode: vi.fn() } }));
const root = { id: 'root', type: 'Module', field_name: null, range: { start_line: 1, start_col: 1, end_line: 3, end_col: 1 }, parent_id: null, child_ids: ['child'], text_preview: 'module', token_ids: [], finding_ids: [] };
const child = { ...root, id: 'child', type: 'Call', parent_id: 'root', child_ids: [], text_preview: 'call' };
describe('ASTSidebar', () => {
  beforeEach(() => vi.mocked(apiClient.getASTNode).mockReset());
  it('loads a missing child on demand and displays server truncation', async () => {
    vi.mocked(apiClient.getASTNode).mockResolvedValue({ root_id: 'child', nodes: [child], truncated: true, node_limit: 1, depth_limit: 1 });
    render(<ASTSidebar analysisId="analysis" initial={{ root_id: 'root', nodes: [root], truncated: false, node_limit: 20, depth_limit: 2 }} capabilities={null} document={null} onSelect={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Expand Module' }));
    await screen.findByRole('button', { name: /Call/ });
    expect(apiClient.getASTNode).toHaveBeenCalledWith('analysis', 'root');
    expect(await screen.findByText(/AST truncated/)).toBeTruthy();
    await waitFor(() => expect(screen.getByRole('button', { name: /Call/ })).toBeTruthy());
  });
});
