import { useEffect, useState, type ReactNode } from 'react';
import type { ASTNodeResponse, CapabilitiesResponse } from '../../api/client';
import type { IDEDocument } from '../state/store';
import { apiClient } from '../../api/client';

type ASTNode = ASTNodeResponse['nodes'][number];
interface Props {
  analysisId: string | null;
  initial: ASTNodeResponse | null;
  capabilities: CapabilitiesResponse | null;
  document: IDEDocument | null;
  onSelect(range: ASTNode['range']): void;
}

export function ASTSidebar({ analysisId, initial, capabilities, document, onSelect }: Props) {
  const [nodes, setNodes] = useState<ASTNode[]>(initial?.nodes ?? []);
  const [rootId, setRootId] = useState(initial?.root_id ?? null);
  const [truncated, setTruncated] = useState(Boolean(initial?.truncated));
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<ASTNode | null>(null);
  useEffect(() => {
    setNodes(initial?.nodes ?? []);
    setRootId(initial?.root_id ?? null);
    setTruncated(Boolean(initial?.truncated));
    setExpanded(new Set());
    setSelected(null);
  }, [analysisId, initial]);
  const expand = async (node: ASTNode) => {
    if (expanded.has(node.id)) {
      setExpanded((old) => new Set([...old].filter((id) => id !== node.id)));
      return;
    }
    setExpanded((old) => new Set(old).add(node.id));
    const known = new Set(nodes.map((item) => item.id));
    if (!analysisId || node.child_ids.every((id) => known.has(id)) || loading.has(node.id)) return;
    setLoading((old) => new Set(old).add(node.id));
    try {
      const response = await apiClient.getASTNode(analysisId, node.id);
      setNodes((old) => [
        ...old.filter((item) => !response.nodes.some((child) => child.id === item.id)),
        ...response.nodes,
      ]);
      setTruncated((old) => old || response.truncated);
    } finally {
      setLoading((old) => new Set([...old].filter((id) => id !== node.id)));
    }
  };
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const loadChild = async (id: string) => {
    if (!analysisId || loading.has(id)) return;
    setLoading((old) => new Set(old).add(id));
    try {
      const response = await apiClient.getASTNode(analysisId, id);
      setNodes((old) => [
        ...old.filter((item) => !response.nodes.some((child) => child.id === item.id)),
        ...response.nodes,
      ]);
      setTruncated((old) => old || response.truncated);
    } finally {
      setLoading((old) => new Set([...old].filter((value) => value !== id)));
    }
  };
  const renderNode = (node: ASTNode, depth: number): ReactNode => (
    <div key={node.id}>
      <div
        className={`ide-ast-row ${selected?.id === node.id ? 'selected' : ''}`}
        style={{ paddingInlineStart: `${8 + depth * 13}px` }}
      >
        {node.child_ids.length > 0 ? (
          <button
            type="button"
            aria-label={`${expanded.has(node.id) ? 'Collapse' : 'Expand'} ${node.type}`}
            onClick={() => void expand(node)}
          >
            {loading.has(node.id) ? '…' : expanded.has(node.id) ? '▾' : '▸'}
          </button>
        ) : (
          <span className="ide-ast-spacer" />
        )}
        <button
          type="button"
          className="ide-ast-name"
          onClick={() => {
            setSelected(node);
            onSelect(node.range);
          }}
          title={`${node.type}${node.field_name ? ` · ${node.field_name}` : ''}`}
        >
          {node.type}
          {node.field_name ? <small> · {node.field_name}</small> : null}
        </button>
      </div>
      {expanded.has(node.id) &&
        node.child_ids.map((id) =>
          byId.get(id) ? (
            renderNode(byId.get(id)!, depth + 1)
          ) : (
            <button
              type="button"
              className="ide-ast-lazy"
              key={id}
              onClick={() => void loadChild(id)}
              disabled={loading.has(id)}
            >
              {loading.has(id) ? 'Loading…' : `Load child ${id}`}
            </button>
          )
        )}
    </div>
  );
  const language = capabilities?.languages.find((item) => item.id === document?.language);
  return (
    <div className="ide-sidebar-scroll ide-ast-sidebar">
      <div className="ide-sidebar-section-label">
        Syntax tree {language ? `· ${language.parser.name ?? language.name}` : ''}
      </div>
      {!initial ? (
        <p className="ide-tree-message">
          {analysisId ? 'AST unavailable for this analysis.' : 'Run Analyze to build the AST.'}
        </p>
      ) : (
        <>
          {truncated && (
            <p className="ide-p4-notice warning">
              AST truncated by the server’s node or depth limit. Expand a node to fetch more.
            </p>
          )}
          {rootId && byId.get(rootId) ? (
            renderNode(byId.get(rootId)!, 0)
          ) : (
            <p className="ide-tree-message">AST root unavailable.</p>
          )}
          {selected && (
            <section className="ide-ast-detail">
              <h3>{selected.type}</h3>
              <dl>
                <dt>Range</dt>
                <dd>
                  {selected.range.start_line}:{selected.range.start_col}–{selected.range.end_line}:
                  {selected.range.end_col}
                </dd>
                <dt>Parent</dt>
                <dd>{selected.parent_id ?? 'Root'}</dd>
                <dt>Children</dt>
                <dd>{selected.child_ids.length}</dd>
                <dt>Linked tokens</dt>
                <dd>{selected.token_ids.length ? selected.token_ids.join(', ') : 'None'}</dd>
                <dt>Linked findings</dt>
                <dd>{selected.finding_ids.length ? selected.finding_ids.join(', ') : 'None'}</dd>
              </dl>
              <pre>{selected.text_preview}</pre>
            </section>
          )}
        </>
      )}
    </div>
  );
}
