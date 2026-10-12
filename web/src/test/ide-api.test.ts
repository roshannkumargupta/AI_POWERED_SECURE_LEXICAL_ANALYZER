import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../api/client';

afterEach(() => vi.unstubAllGlobals());
describe('P1 API client', () => {
  it('maps structured API errors and sends session credentials', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: 'stale_source', message: 'Source changed' } }), { status: 409, headers: { 'Content-Type': 'application/json' } }));
    vi.stubGlobal('fetch', fetchMock);
    await expect(apiClient.getHealth()).rejects.toMatchObject({ code: 'stale_source', message: 'Source changed', status: 409 });
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: 'include' });
  });
  it('preserves abort errors and classifies network errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    await expect(apiClient.getHealth()).rejects.toMatchObject({ code: 'network_error', message: 'offline', status: 0 });
  });
});
