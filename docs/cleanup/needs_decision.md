# Items Requiring Human Architectural Decisions — CLEAN-1

**Audit Date:** October 10, 2026  
**Scope:** Phase CLEAN-1  

---

## 1. Preserved Historical & Large Artifacts

| Item / Directory | Size | Reason Held | Proposed Action for Phase CLEAN-2 / Future |
|---|---|---|---|
| `legacy/senior-part1/` | ~12.4 MB | Historical senior prototype Python codebase | Kept strictly read-only per rule 4 and `PROJECT_SPEC.md` |
| `legacy/senior-part2/` | ~3.8 MB | Historical senior prototype Java codebase (MIT licensed) | Kept strictly read-only per rule 4 and `PROJECT_SPEC.md` |
| `src/apsla/ml/artifacts/` | ~18.2 MB | 16 pre-trained joblib and PyTorch model artifacts across languages | Preserved: runtime models required for ML inference engine; schema hash verified |
| `data/raw/` & `data/sources/` | ~4.2 MB | Benchmark attack corpora, Unicode confusables tables | Preserved: ground truth data assets; zero modification policy |
| `data/external/` | ~0.8 MB | Realistic external evaluation snippets across 4 languages | Preserved: test ground truth |

---

## 2. Dynamic Registry & Entry Point Items

The following candidates were audited by vulture / dead-code heuristics but confirmed active via dynamic reflection:
- `LanguagePlugin` implementations in `src/apsla/languages/*`: loaded dynamically via `src/apsla/languages/registry.py`.
- Security rule instances: discovered via `Plugin.rules()` call in `registry.py` and `pipeline.py`.
- Fix generators: registered via `Plugin.fix_generators()`.
- Pydantic models: dynamically serialized by FastAPI endpoints.
- CLI subcommands: discovered via Typer reflection.

All dynamic items are preserved with zero risk of broken runtime imports.
