const { useState, useCallback } = React;

const API = "http://localhost:8000";

// ── Colour helpers ─────────────────────────────────────────────
const LABEL_STYLE = {
  SAFE:       { bg: "#dcfce7", color: "#166534", border: "#86efac" },
  SUSPICIOUS: { bg: "#fef9c3", color: "#854d0e", border: "#fde047" },
  MALICIOUS:  { bg: "#fee2e2", color: "#991b1b", border: "#fca5a5" },
};

const Badge = ({ label }) => {
  const s = LABEL_STYLE[label] || LABEL_STYLE.SAFE;
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 999, fontSize: 11, fontWeight: 700,
      background: s.bg, color: s.color,
      border: `1px solid ${s.border}`, whiteSpace: "nowrap"
    }}>
      {label}
    </span>
  );
};

// ── Sample inputs ──────────────────────────────────────────────
const SAMPLES = {
  "Clean Code": `def add(a, b):\n    return a + b\n\nresult = add(3, 7)\nprint(result)`,
  "Homoglyph":  `admin = 1\n\u0430dmin = 2   # Cyrillic 'a'`,
  "SQL Injection": `query = f"SELECT * FROM users WHERE id = {user_id}"\ncursor.execute(query)`,
  "exec/eval":  `exec("__import__('os').system('id')")`,
  "Taint Flow": `user_input = input("cmd: ")\nos.system(user_input)`,
  "Zero-Width": `safe\u200bVar = 1\nnor\u200bmal = 2`,
};

// ── Main App ───────────────────────────────────────────────────
function App() {
  const [source,   setSource]   = useState(SAMPLES["Clean Code"]);
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [filter,   setFilter]   = useState("ALL");  // ALL / SUSPICIOUS / MALICIOUS
  const [search,   setSearch]   = useState("");

  const analyze = useCallback(async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const res  = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, filename: "<editor>" }),
      });
      const data = await res.json();
      if (data.error) setError(data.error);
      else setResult(data);
    } catch (e) {
      setError("Cannot reach API. Is the server running?\nuvicorn frontend.api:app --reload");
    }
    setLoading(false);
  }, [source]);

  // Filtered token list
  const visibleTokens = result?.tokens?.filter(t => {
    if (filter !== "ALL" && t.label !== filter) return false;
    if (search && !t.token.toLowerCase().includes(search.toLowerCase())
               && !t.token_type.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  }) ?? [];

  return (
    <div style={{ minHeight: "100vh", padding: 24, maxWidth: 1300, margin: "0 auto" }}>

      {/* ── Header ─────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: "#1e3a5f" }}>
          🛡 AI-Powered Secure Lexical Analyzer
        </h1>
        <p style={{ color: "#64748b", marginTop: 4, fontSize: 14 }}>
          Paste Python source code and detect Unicode attacks, injections, and obfuscations.
        </p>
      </div>

      {/* ── Two-column layout ──────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

        {/* LEFT — Editor */}
        <div>
          {/* Sample buttons */}
          <div style={{ marginBottom: 8, display: "flex", flexWrap: "wrap", gap: 6 }}>
            {Object.keys(SAMPLES).map(name => (
              <button key={name}
                onClick={() => setSource(SAMPLES[name])}
                style={{
                  padding: "4px 10px", fontSize: 12, borderRadius: 6, cursor: "pointer",
                  background: "#e2e8f0", border: "1px solid #cbd5e1", color: "#334155"
                }}>
                {name}
              </button>
            ))}
          </div>

          <textarea
            value={source}
            onChange={e => setSource(e.target.value)}
            spellCheck={false}
            style={{
              width: "100%", height: 340, padding: 14,
              fontFamily: "Consolas, monospace", fontSize: 13, lineHeight: 1.6,
              background: "#1e1e2e", color: "#cdd6f4",
              border: "1px solid #334155", borderRadius: 10, resize: "vertical",
              outline: "none"
            }}
            placeholder="Paste Python code here..."
          />

          <button
            onClick={analyze}
            disabled={loading}
            style={{
              marginTop: 12, width: "100%", padding: "12px 0",
              fontSize: 15, fontWeight: 700, borderRadius: 8, cursor: "pointer",
              background: loading ? "#94a3b8" : "#1e3a5f",
              color: "#fff", border: "none",
              transition: "background 0.2s"
            }}>
            {loading ? "Analysing…" : "▶  Analyse"}
          </button>

          {/* Error box */}
          {error && (
            <pre style={{
              marginTop: 12, padding: 12, background: "#fee2e2", color: "#991b1b",
              borderRadius: 8, fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-word"
            }}>{error}</pre>
          )}
        </div>

        {/* RIGHT — Summary + Taint */}
        <div>
          {result ? (
            <>
              {/* Summary cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
                {[
                  { label: "Total",      value: result.total_tokens, bg: "#f1f5f9", color: "#334155" },
                  { label: "Safe",       value: result.safe,         bg: "#dcfce7", color: "#166534" },
                  { label: "Suspicious", value: result.suspicious,   bg: "#fef9c3", color: "#854d0e" },
                  { label: "Malicious",  value: result.malicious,    bg: "#fee2e2", color: "#991b1b" },
                ].map(c => (
                  <div key={c.label} style={{
                    background: c.bg, borderRadius: 10, padding: "14px 10px", textAlign: "center"
                  }}>
                    <div style={{ fontSize: 28, fontWeight: 800, color: c.color }}>{c.value}</div>
                    <div style={{ fontSize: 12, color: c.color, marginTop: 2 }}>{c.label}</div>
                  </div>
                ))}
              </div>

              {/* Taint log */}
              {result.taint_log?.length > 0 && (
                <div style={{
                  background: "#fff7ed", border: "1px solid #fed7aa",
                  borderRadius: 10, padding: 12, marginBottom: 16
                }}>
                  <div style={{ fontWeight: 700, fontSize: 13, color: "#9a3412", marginBottom: 6 }}>
                    ⚠ Taint Analysis
                  </div>
                  {result.taint_log.map((entry, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#7c2d12", fontFamily: "monospace" }}>
                      {entry}
                    </div>
                  ))}
                </div>
              )}

              {/* Quick stat bar */}
              <div style={{ marginBottom: 12, height: 8, borderRadius: 999, overflow: "hidden",
                            display: "flex", background: "#e2e8f0" }}>
                {[
                  { val: result.safe,       color: "#22c55e" },
                  { val: result.suspicious, color: "#eab308" },
                  { val: result.malicious,  color: "#ef4444" },
                ].map((seg, i) => (
                  <div key={i} style={{
                    width: `${(seg.val / result.total_tokens) * 100}%`,
                    background: seg.color, transition: "width 0.4s"
                  }}/>
                ))}
              </div>

              <p style={{ fontSize: 12, color: "#64748b" }}>
                {result.malicious > 0
                  ? `⛔ ${result.malicious} malicious token${result.malicious > 1 ? "s" : ""} detected.`
                  : result.suspicious > 0
                  ? `⚠ ${result.suspicious} suspicious token${result.suspicious > 1 ? "s" : ""} flagged.`
                  : "✅ No threats detected."}
              </p>
            </>
          ) : (
            <div style={{
              height: 200, display: "flex", alignItems: "center", justifyContent: "center",
              background: "#f8fafc", borderRadius: 12, border: "1px dashed #cbd5e1",
              color: "#94a3b8", fontSize: 14
            }}>
              Click Analyse to see results
            </div>
          )}
        </div>
      </div>

      {/* ── Token Table ────────────────────────────────────── */}
      {result && (
        <div style={{ marginTop: 24 }}>
          <div style={{ display: "flex", gap: 10, marginBottom: 12, alignItems: "center" }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "#1e3a5f" }}>Token Analysis</h2>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              {/* Filter buttons */}
              {["ALL", "SUSPICIOUS", "MALICIOUS"].map(f => (
                <button key={f} onClick={() => setFilter(f)}
                  style={{
                    padding: "4px 12px", borderRadius: 6, fontSize: 12, cursor: "pointer",
                    fontWeight: filter === f ? 700 : 400,
                    background: filter === f ? "#1e3a5f" : "#e2e8f0",
                    color: filter === f ? "#fff" : "#475569",
                    border: "none"
                  }}>
                  {f}
                </button>
              ))}
              {/* Search */}
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search token…"
                style={{
                  padding: "4px 10px", borderRadius: 6, fontSize: 12,
                  border: "1px solid #cbd5e1", outline: "none", width: 140
                }}
              />
            </div>
          </div>

          <div style={{ overflowX: "auto", borderRadius: 10, border: "1px solid #e2e8f0" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#1e3a5f", color: "#fff" }}>
                  {["Line", "Token", "Type", "Label", "Score", "Entropy", "Reasons"].map(h => (
                    <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontWeight: 600, whiteSpace: "nowrap" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleTokens.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: 24, textAlign: "center", color: "#94a3b8" }}>
                      No tokens match the current filter.
                    </td>
                  </tr>
                ) : visibleTokens.map((tok, i) => {
                  const s = LABEL_STYLE[tok.label] || LABEL_STYLE.SAFE;
                  const rowBg = tok.label === "MALICIOUS" ? "#fff5f5"
                              : tok.label === "SUSPICIOUS" ? "#fffdf0" : "#fff";
                  return (
                    <tr key={i} style={{ background: i % 2 === 0 ? rowBg : "#fafafa",
                                         borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "8px 12px", color: "#94a3b8" }}>{tok.line + 1}</td>
                      <td style={{ padding: "8px 12px" }}>
                        <code style={{
                          background: "#1e1e2e", color: "#cdd6f4",
                          padding: "2px 6px", borderRadius: 4, fontSize: 12
                        }}>
                          {tok.token.length > 30 ? tok.token.slice(0, 30) + "…" : tok.token}
                        </code>
                        {tok.recovered !== tok.token && (
                          <span style={{ fontSize: 11, color: "#f59e0b", marginLeft: 6 }}>
                            → {tok.recovered}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: "8px 12px", color: "#64748b", fontSize: 12 }}>{tok.token_type}</td>
                      <td style={{ padding: "8px 12px" }}><Badge label={tok.label} /></td>
                      <td style={{ padding: "8px 12px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <div style={{ width: 50, height: 6, background: "#e2e8f0", borderRadius: 999, overflow: "hidden" }}>
                            <div style={{
                              width: `${tok.score * 100}%`, height: "100%",
                              background: tok.score > 0.7 ? "#ef4444" : tok.score > 0.4 ? "#eab308" : "#22c55e"
                            }}/>
                          </div>
                          <span style={{ fontSize: 11, color: "#64748b" }}>{tok.score.toFixed(2)}</span>
                        </div>
                      </td>
                      <td style={{ padding: "8px 12px", color: "#64748b", fontSize: 12 }}>
                        {tok.entropy ?? "—"}
                      </td>
                      <td style={{ padding: "8px 12px", maxWidth: 300 }}>
                        {tok.reasons.length > 0 ? (
                          <ul style={{ paddingLeft: 14, margin: 0 }}>
                            {tok.reasons.map((r, ri) => (
                              <li key={ri} style={{ fontSize: 11, color: s.color }}>{r}</li>
                            ))}
                          </ul>
                        ) : (
                          <span style={{ color: "#94a3b8", fontSize: 11 }}>—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p style={{ marginTop: 8, fontSize: 12, color: "#94a3b8" }}>
            Showing {visibleTokens.length} of {result.total_tokens} tokens
          </p>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);