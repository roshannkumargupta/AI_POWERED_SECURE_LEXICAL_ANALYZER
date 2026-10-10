# Dead-Code Candidates Register — CLEAN-1

**Audit Date:** October 10, 2026  
**Scope:** Phase CLEAN-1  

---

## Candidate Audit Table

| Item | Tool / Source | Evidence | Dynamic-Use Risk | Action | Rationale |
|---|---|---|---|---|---|
| `scripts/generate_inventory.py:Any` | Ruff F401 | Unused type import | None | Deleted | Fixed in `b7b8b06` |
| `scripts/generate_inventory.py:sha,stage` | Ruff F841 | Unused unpack assignments | None | Deleted | Fixed in `b7b8b06` |
| `src/apsla/languages/registry.py` plugin lookups | Vulture | Dynamic dictionary registration | High | Keep | Loaded dynamically at runtime by language ID |
| `src/apsla/rules/*.py` rule subclasses | Vulture | Dynamic plugin registry collection | High | Keep | Discovered by `plugin.rules()` protocol |
| `src/apsla/fixes/*.py` fix generators | Vulture | Dynamic generator map | High | Keep | Discovered by `plugin.fix_generators()` |
| `src/apsla/models.py` Pydantic fields | Vulture | Attribute access via FastAPI / Pydantic | High | Keep | Public REST API JSON schema contract |
| `src/apsla/server/app.py` route handlers | Vulture | Framework decorator callbacks | High | Keep | FastAPI endpoint entrypoints |
| `src/apsla/cli.py` CLI commands | Vulture | Typer command callbacks | High | Keep | Typer CLI commands |
| `web/src/state/*.ts` action creators | Knip heuristic | Reducer action handlers | High | Keep | Action dispatchers in React state |
| `web/public/theme-init.js` | Knip heuristic | Direct script tag in index.html | High | Keep | Critical pre-paint theme initializer |
| `web/src/monaco/workers.ts` | Knip heuristic | Monaco web worker instantiation | High | Keep | Monaco syntax highlighting and worker threads |
