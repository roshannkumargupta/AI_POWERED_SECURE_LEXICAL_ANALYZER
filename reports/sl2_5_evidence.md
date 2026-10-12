# SL2-5 evidence — provider, gateway, agent integration

Date: 2026-10-12

## Environment and provider probe

Command:

```powershell
$env:PYTHONPATH='src'; python -c "from apsla.llm.local_ollama import get_agent_status; print(get_agent_status())"
```

Output:

```text
{'mode': 'off', 'ollama_reachable': False, 'model': 'qwen2.5-coder:3b', 'model_present': False, 'fallback_active': False, 'message': 'Ollama is not running at http://127.0.0.1:11434'}
```

The provider/model exercised in this environment was **none**: Ollama was unreachable and `qwen2.5-coder:3b` was not present. Remote provider configuration and consent were tested with unit-level doubles, not a live endpoint. To enable the local provider, start Ollama and run `ollama pull qwen2.5-coder:3b`. No live AI output is claimed.

## Changes

- Added `src/apsla/agents/provider_v2.py`: provider protocol and typed failures, Ollama and OpenAI-compatible adapters, bounded 15-second HTTP timeout, two attempts with one schema-repair prompt, 512 KiB request cap, 2,048 output-token request cap, 256 KiB response cap, schema validation, and secret redaction.
- Added an in-memory session consent set; `/api/ai/consent` writes/revokes it and remote AI operations require both the API consent flag and stored consent. Loopback OpenAI-compatible endpoints are treated as local.
- Added a structured `PatchProposal` adapter on the existing Fix Agent so deterministic candidates carry target, edits/diff, rationale, outcome, assumptions and risks as unapplied drafts.
- Wrapped existing in-memory agent tools in the schema-checked `ToolGateway`, with per-tool operation permissions, a 32-call agent-session budget, and bounded wait. Shell, filesystem, network and policy tools are not allowed.
- Added `/api/ai/explain`, `/api/ai/generate` and `/api/agent/events`. Explain selects evidence from fresh deterministic analysis. Generate returns a draft, analyzes it with the existing pipeline, marks every requirement unverified, and does not execute candidate code.
- Added a per-tab provider/location/consent indicator in the existing UI. Existing API routes are retained.
- Added OpenAPI reference and golden schema for the additive API routes.

## Verification

Ruff command:

```powershell
ruff check src/apsla/agents/provider_v2.py src/apsla/agents/tools.py src/apsla/agents/fix_agent.py src/apsla/agents/explain_agent.py src/apsla/server/app.py src/apsla/server/schemas.py tests/unit/test_sl2_5_provider.py
```

Output: `All checks passed!`

Pytest command (298 relevant tests):

```powershell
$env:PYTHONPATH='src'; pytest tests/unit/test_sl2_5_provider.py tests/unit/test_sl2_v2.py tests/unit/test_phase15_agents.py tests/security/test_agent_injection.py -k 'not invariant_b_mode_off' --basetemp=.pytest_tmp_sl25 -q -rA
```

Output: `298 passed` (provider/gateway/event tests, grounding rejection of an injection-obedient explanation, structured Fix Agent proposal, generated-candidate analysis adapter, SL2-1 contract/regression fixtures, agent invariants, and injection defenses). The `invariant_b_mode_off` case was excluded because it directly invokes the existing async HTTP handler and hangs in this Windows sandbox; this is the same `asyncio.to_thread`/local transport limitation documented by preceding SL2 phases. A broader repo pytest pass is not claimed. An initial collection without `PYTHONPATH=src` failed to import the package; pytest also needs a workspace-local basetemp because system temp directory creation is blocked.

OpenAPI generation command imported `app.openapi()` and wrote `docs/api_v2.md` plus `tests/golden/openapi_schema.json`. Output: `OpenAPI paths recorded: 24`; direct schema inspection confirmed `/api/ai/explain`, `/api/ai/generate`, and `/api/agent/events` are present.

UI build command: `npm run build` (from `web`). Output included `✓ 2677 modules transformed.` and `✓ built in 1m 17s`, exit code 0. Vite emitted its existing large-chunk warning for the 3.64 MB main JS bundle; it did not fail the build.

Live Ollama explain/generate was unavailable as noted above. Live remote provider behavior was not tested. HTTP end-to-end operation of the new AI routes is not claimed; their generated API contracts and provider/gateway primitives were checked independently.
