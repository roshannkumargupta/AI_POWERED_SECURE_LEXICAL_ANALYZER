import { useEffect, useMemo, useState } from 'react';
import { apiClient, type AgentEvent } from '../../api/client';

export function AgentActivityPanel({ onOpenEvent }: { onOpenEvent(event: AgentEvent): void }) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    let timer = 0;
    const poll = async () => {
      try { setEvents(await apiClient.getAgentEvents(undefined, controller.signal)); setError(null); }
      catch (reason) { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Could not load agent events.'); }
      if (!controller.signal.aborted) timer = window.setTimeout(poll, 1200);
    };
    void poll();
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, []);
  const filtered = useMemo(() => events.filter(event => `${event.timestamp} ${event.agent} ${event.action} ${event.tool ?? ''} ${event.decision_source} ${event.outcome} ${event.error ?? ''} ${event.argument_summary}`.toLowerCase().includes(filter.toLowerCase())), [events, filter]);
  const clear = async () => {
    setClearing(true);
    try { await apiClient.clearAgentEvents(); setEvents([]); setError(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not clear agent events.'); }
    finally { setClearing(false); }
  };
  return <section className="ide-ai-content" aria-label="Agent activity"><header><strong>Agent Activity</strong><input aria-label="Filter agent events" placeholder="Filter events" value={filter} onChange={event => setFilter(event.target.value)} /><button type="button" disabled={!events.length || clearing} title={!events.length ? 'There are no session events to clear.' : 'Clear this session’s event history'} onClick={() => void clear()}>{clearing ? 'Clearing…' : 'Clear'}</button></header>{error && <p role="alert">{error}</p>}{!filtered.length ? <p>No events yet</p> : <ol className="ide-agent-events">{filtered.map(event => <li key={event.id}><time dateTime={event.timestamp}>{new Date(event.timestamp).toLocaleString()}</time><b>{event.agent}</b><span>{event.action}</span><span>{event.tool ?? 'Internal'}</span><span>{event.decision_source}</span><strong>{event.outcome}</strong><span>{event.duration.toFixed(1)} ms</span><small className="ide-agent-arguments">{event.argument_summary}</small>{event.subject_type && <button type="button" className="ide-agent-subject" onClick={() => onOpenEvent(event)}>Open explained {event.subject_type}</button>}{event.error && <p>{event.error}</p>}</li>)}</ol>}</section>;
}
