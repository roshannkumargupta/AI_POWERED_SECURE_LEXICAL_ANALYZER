import { useEffect, useMemo, useState } from 'react';
import { apiClient, type AgentEvent } from '../../api/client';

export function AgentActivityPanel({ operationId }: { operationId: string | null }) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [filter, setFilter] = useState('');
  useEffect(() => {
    setEvents([]);
    if (!operationId) return;
    const controller = new AbortController();
    let timer = 0;
    const poll = async () => {
      try { setEvents(await apiClient.getAgentEvents(operationId, controller.signal)); } catch { /* Keep the last real event list visible while polling. */ }
      if (!controller.signal.aborted) timer = window.setTimeout(poll, 1200);
    };
    void poll();
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [operationId]);
  const filtered = useMemo(() => events.filter(event => `${event.timestamp} ${event.agent} ${event.action} ${event.tool ?? ''} ${event.decision_source} ${event.outcome} ${event.error ?? ''}`.toLowerCase().includes(filter.toLowerCase())), [events, filter]);
  return <section className="ide-ai-content" aria-label="Agent activity"><header><strong>Agent Activity</strong><input aria-label="Filter agent events" placeholder="Filter events" value={filter} onChange={event => setFilter(event.target.value)} /></header>{!filtered.length ? <p>No events yet</p> : <ol className="ide-agent-events">{filtered.map(event => <li key={event.id}><time>{event.timestamp}</time><b>{event.agent}</b><span>{event.action}</span><span>{event.tool ?? 'Internal'}</span><span>{event.decision_source}</span><strong>{event.outcome}</strong><span>{event.duration.toFixed(1)} ms</span>{event.error && <p>{event.error}</p>}</li>)}</ol>}</section>;
}
