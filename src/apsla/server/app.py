"""FastAPI REST HTTP service for SecureLex IDE."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Final

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from apsla import __version__
from apsla.languages import registry
from apsla.models import AnalysisResult, Fix
from apsla.pipeline import Analyzer
from apsla.server.cache import ANALYSIS_CACHE
from apsla.server.samples import get_sample, get_samples
from apsla.server.schemas import (
    AgentStatusResponse,
    AnalyzeRequest,
    FeedbackRequest,
    FeedbackResponse,
    FixAllRequest,
    FixAllResponse,
    FixRequest,
    FixResponse,
    HealthResponse,
    LanguageInfo,
    LLMExplainRequest,
    LLMExplainResponse,
    LLMFixRequest,
    LLMFixResponse,
    LLMStatusResponse,
    MLInsightsRequest,
    MLInsightsResponse,
    SampleItem,
    SkippedFixItem,
)

logger = logging.getLogger("apsla.server")

MAX_SOURCE_BYTES: Final[int] = 512 * 1024  # 512 KB limit
WEB_DIST_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist"

# Initialize application
app = FastAPI(
    title="SecureLex IDE API",
    version=__version__,
    description="High-performance code security analysis and verified automated repair HTTP service.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Policy: Restricted strictly to Vite frontend dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Safely log server exceptions without leaking stack traces to the client."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    error_id = str(uuid.uuid4())[:8]
    logger.exception(
        "Unhandled error [Error-ID: %s] on %s %s: %s",
        error_id,
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error_id": error_id},
    )


def _validate_payload_size(source: str) -> None:
    """Enforces strict 512 KB source code size limit."""
    payload_size = len(source.encode("utf-8"))
    if payload_size > MAX_SOURCE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Source payload size ({payload_size} bytes) exceeds the 512 KB limit.",
        )


def _resolve_language(language: str | None, filename: str | None, source: str) -> str:
    """Determines target language identifier, falling back to auto-detection."""
    # Ensure default plugins are loaded
    registry.get("python")

    if language and language.strip():
        lang_key = language.strip().lower()
        if lang_key in ("py", "python"):
            return "python"
        plugin = registry.get(lang_key)
        if plugin is not None:
            return plugin.id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown or unsupported programming language: '{language}'.",
        )

    # Auto-detect from filename or content
    target_name = filename or "snippet.py"
    detected = registry.detect(target_name, source)
    if detected is not None:
        return detected.id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not detect language. Please specify a supported language (e.g. 'python').",
    )


# ── API Router (/api) ─────────────────────────────────────────────────────────

api_router = APIRouter(prefix="/api")


@api_router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Return service health status, active version, and ML engine telemetry."""
    from apsla.ml.infer import MLInferenceEngine

    engine = MLInferenceEngine()
    return HealthResponse(
        status="ok",
        version=__version__,
        ml_mode=engine.get_mode(),
        ml_model_id=engine.get_model_id(),
    )


@api_router.get("/languages", response_model=list[LanguageInfo])
async def get_languages() -> list[LanguageInfo]:
    """List registered language plugins and editor syntax identifiers."""
    registry.get("python")  # Ensure standard plugins are loaded
    plugins = registry.list_plugins()
    return [
        LanguageInfo(
            id=p.id,
            display_name=p.display_name,
            extensions=list(p.extensions),
            monaco_id=p.monaco_id,
        )
        for p in plugins
    ]


@api_router.post("/analyze", response_model=AnalysisResult)
async def analyze_code(req: AnalyzeRequest) -> AnalysisResult:
    """Run full hybrid static security analysis with pure caching and timeout."""
    _validate_payload_size(req.source)
    target_filename = req.filename or "<editor>"
    target_language = _resolve_language(req.language, target_filename, req.source)

    analysis_opts = {
        "fixes": req.options.fixes,
        "ml": req.options.ml,
        "agent": req.options.agent,
    }

    # Check LRU cache (pure function of source + language + filename + options)
    cache_key = ANALYSIS_CACHE.compute_key(
        req.source, target_language, target_filename, analysis_opts
    )
    raw_result = ANALYSIS_CACHE.get(cache_key)

    if raw_result is None:
        analyzer = Analyzer()

        def _perform_analysis() -> AnalysisResult:
            return analyzer.analyze(
                source=req.source,
                language=target_language,
                filename=target_filename,
                options=analysis_opts,
            )

        try:
            raw_result = await asyncio.wait_for(
                asyncio.to_thread(_perform_analysis),
                timeout=10.0,
            )
        except TimeoutError:
            logger.error("Analysis timed out after 10.0 seconds for file %s", target_filename)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Analysis timed out after 10 seconds",
            ) from None

        ANALYSIS_CACHE.put(cache_key, raw_result)

    result = raw_result

    # Handle include_suppressed
    if not req.options.include_suppressed:
        active_findings = [f for f in result.findings if not f.suppressed]
        if len(active_findings) != len(result.findings):
            from apsla.scoring import create_analysis_summary

            new_summary = create_analysis_summary(findings=active_findings, tokens=result.tokens)
            result = result.model_copy(update={"findings": active_findings, "summary": new_summary})

    # Handle include_tokens
    if not req.options.include_tokens:
        result = result.model_copy(update={"tokens": []})

    # Agentic execution layer (Phase 15)
    agent_mode = (req.options.agent or "off").lower()
    if agent_mode in {"rules", "local"}:
        if not result.trace:
            from apsla.agents.orchestrator import AgentOrchestrator
            from apsla.scoring import create_analysis_summary

            orch = AgentOrchestrator(mode=agent_mode)
            agent_findings, trace, agent_meta = orch.run(
                source=req.source,
                language=target_language,
                filename=target_filename,
                initial_findings=result.findings,
            )
            new_summary = create_analysis_summary(findings=agent_findings, tokens=result.tokens)
            result = result.model_copy(
                update={
                    "findings": agent_findings,
                    "summary": new_summary,
                    "trace": [
                        s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in trace
                    ],
                    "agent_meta": agent_meta,
                }
            )
    else:
        result = result.model_copy(update={"trace": [], "agent_meta": {"mode": "off"}})

    return result


@api_router.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status_endpoint() -> AgentStatusResponse:
    """Return local agent status and local model availability."""
    from apsla.llm.local_ollama import get_agent_status

    status_data = get_agent_status()
    return AgentStatusResponse(**status_data)


@api_router.post("/agent/analyze", response_model=AnalysisResult)
async def analyze_code_agent(req: AnalyzeRequest) -> AnalysisResult:
    """Run code analysis with agent layer enabled (defaults to rules if set to off)."""
    if (req.options.agent or "off") == "off":
        req.options.agent = "rules"
    return await analyze_code(req)


@api_router.post("/fix", response_model=FixResponse)
async def apply_single_fix(req: FixRequest) -> FixResponse:
    """Apply and verify a specific fix proposal."""
    _validate_payload_size(req.source)
    lang = _resolve_language(req.language, req.filename, req.source)

    analyzer = Analyzer()
    initial_res = analyzer.analyze(
        req.source,
        language=lang,
        filename=req.filename,
        options={"fixes": True, "ml": False},
    )

    target_fix: Fix | None = None
    for f in initial_res.findings:
        if f.id == req.finding_id:
            for fix in f.fixes:
                if fix.id == req.fix_id:
                    target_fix = fix
                    break
        if target_fix:
            break

    # Fallback search across all findings by fix_id
    if target_fix is None:
        for f in initial_res.findings:
            for fix in f.fixes:
                if fix.id == req.fix_id:
                    target_fix = fix
                    break
            if target_fix:
                break

    if target_fix is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fix '{req.fix_id}' or finding '{req.finding_id}' not found.",
        )

    from apsla.fixes.edits import apply_edits, unified_diff

    new_source = apply_edits(req.source, target_fix.edits)
    diff_text = unified_diff(req.source, new_source, filename=req.filename)
    new_res = analyzer.analyze(
        new_source,
        language=lang,
        filename=req.filename,
        options={"fixes": True},
    )

    return FixResponse(
        new_source=new_source,
        diff=diff_text,
        verification=target_fix.verification,
        new_result=new_res,
    )


@api_router.post("/fix-all", response_model=FixAllResponse)
async def apply_all_fixes(req: FixAllRequest) -> FixAllResponse:
    """Iteratively apply all safe and verified fixes up to 3 passes."""
    _validate_payload_size(req.source)
    lang = _resolve_language(req.language, req.filename, req.source)

    from apsla.fixes.engine import fix_all

    new_source, applied, skipped_dict, diff_text, score_before, score_after = fix_all(
        req.source,
        language=lang,
        filename=req.filename,
        allow_review=req.allow_review,
    )

    skipped_items = [SkippedFixItem(fix_id=k, reason=v) for k, v in skipped_dict.items()]

    return FixAllResponse(
        new_source=new_source,
        applied=applied,
        skipped=skipped_items,
        diff=diff_text,
        score_before=score_before,
        score_after=score_after,
    )


@api_router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(req: FeedbackRequest) -> FeedbackResponse:
    """Record user false-positive report to local append-only feedback storage."""
    from apsla.feedback.store import save_feedback

    record = req.model_dump()
    saved = save_feedback(record)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record false-positive feedback.",
        )

    # Invalidate cache so future analyses reflect suppression immediately
    ANALYSIS_CACHE.clear()
    return FeedbackResponse(saved=True)


@api_router.get("/samples", response_model=None)
async def list_samples(language: str | None = None, meta: bool = False) -> list[dict[str, object]]:
    """Retrieve pre-bundled interactive code samples."""
    records = [
        sample.model_dump(exclude={"code"} if meta else None) for sample in get_samples(language)
    ]
    return records


@api_router.get("/samples/{sample_id}", response_model=SampleItem)
async def sample_detail(sample_id: str) -> SampleItem:
    """Retrieve one shipped sample by ID."""
    sample = get_sample(sample_id)
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return sample


@api_router.post("/ml/insights", response_model=MLInsightsResponse)
async def get_ml_insights(req: MLInsightsRequest) -> MLInsightsResponse:
    """Compute per-feature-group occlusion explainability for a token window."""
    _validate_payload_size(req.source)
    lang = _resolve_language(req.language, "source.py", req.source)
    from apsla.ml.infer import MLInferenceEngine

    engine = MLInferenceEngine(language=lang)
    if not engine.is_available(language=lang) or engine.model_wrapper is None:
        return MLInsightsResponse(ml_mode="off")
    plugin = registry.get(lang)
    tokens = plugin.lex(req.source) if plugin else []

    if not tokens or not (0 <= req.token_index < len(tokens)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token index {req.token_index} is out of bounds (0..{max(0, len(tokens) - 1)}).",
        )

    import numpy as np

    from apsla.ml.explain import explain_token_prediction
    from apsla.ml.features import extract_file_features
    from apsla.ml.windows import build_token_windows

    feats, lang_id = extract_file_features(tokens, language=lang)
    w3d, wflat, _, _ = build_token_windows(tokens, feats)

    window_3d = w3d[req.token_index : req.token_index + 1]
    window_flat = wflat[req.token_index : req.token_index + 1]

    probs = engine.model_wrapper.predict_proba(
        window_3d,
        window_flat,
        lang_ids=np.array([lang_id]),
        temperature=engine.temperature,
    )[0]

    drops = explain_token_prediction(
        engine.model_wrapper,
        window_3d,
        window_flat,
        target_class=2,
        lang_id=lang_id,
        temperature=engine.temperature,
    )

    pred_label = ["SAFE", "SUSPICIOUS", "MALICIOUS"][int(np.argmax(probs))]

    return MLInsightsResponse(
        ml_mode="on",
        token_index=req.token_index,
        token_text=tokens[req.token_index].text,
        predicted_label=pred_label,
        probabilities={
            "SAFE": round(float(probs[0]), 4),
            "SUSPICIOUS": round(float(probs[1]), 4),
            "MALICIOUS": round(float(probs[2]), 4),
        },
        feature_group_drops=drops,
    )


@api_router.get("/llm/status", response_model=LLMStatusResponse)
async def get_llm_status() -> LLMStatusResponse:
    """Check whether an LLM provider is configured in environment variables."""
    from apsla.llm.provider import get_llm_provider

    provider = get_llm_provider()
    return LLMStatusResponse(
        configured=provider.is_configured(),
        provider=provider.provider_name,
    )


@api_router.post("/llm/fix", response_model=LLMFixResponse)
async def request_llm_fix(req: LLMFixRequest) -> LLMFixResponse:
    """Request and shadow-verify an AI-suggested remediation fix."""
    from apsla.fixes.verifier import verify_fix
    from apsla.llm.provider import get_llm_provider
    from apsla.models import Finding, Label, Range, Severity
    from apsla.pipeline import Analyzer

    provider = get_llm_provider()
    if not provider.is_configured():
        return LLMFixResponse(fixes=[], notes="No LLM provider configured.")

    target_finding: Finding | None = None
    try:
        analyzer = Analyzer()
        res = analyzer.analyze(
            req.source, language=req.language, options={"fixes": False, "ml": False}
        )
        for f in res.findings:
            if f.id == req.finding_id or f.rule_id == req.rule_id:
                target_finding = f
                break
    except Exception:
        pass

    if target_finding is None:
        start_l = req.start_line or 1
        start_c = req.start_col or 1
        target_finding = Finding(
            id=req.finding_id,
            rule_id=req.rule_id,
            title=f"Finding {req.rule_id}",
            cwe="CWE-Other",
            severity=Severity.HIGH,
            label=Label.MALICIOUS,
            confidence=0.9,
            range=Range(
                start_line=start_l, start_col=start_c, end_line=start_l, end_col=start_c + 10
            ),
            message=f"Remediate {req.rule_id}",
            explanation="",
        )

    suggested_fixes = provider.suggest_fix(req.source, target_finding)
    verified_fixes = []

    for fix in suggested_fixes:
        fix_with_kind = fix.model_copy(update={"kind": "llm"})
        verified = verify_fix(req.source, fix_with_kind, target_finding, language=req.language)
        verified_fixes.append(verified)

    return LLMFixResponse(fixes=verified_fixes)


@api_router.post("/llm/explain", response_model=LLMExplainResponse)
async def request_llm_explain(req: LLMExplainRequest) -> LLMExplainResponse:
    """Request plain-English explanation from configured LLM."""
    from apsla.llm.provider import get_llm_provider
    from apsla.models import Finding, Label, Range, Severity

    provider = get_llm_provider()
    if not provider.is_configured():
        from apsla.rules.explanations import get_rule_template

        tmpl = get_rule_template(req.rule_id)
        return LLMExplainResponse(explanation=tmpl.what if tmpl else req.message)

    finding = Finding(
        id=req.finding_id,
        rule_id=req.rule_id,
        title=f"Finding {req.rule_id}",
        cwe="CWE-Other",
        severity=Severity.HIGH,
        label=Label.MALICIOUS,
        confidence=0.9,
        range=Range(start_line=1, start_col=1, end_line=1, end_col=1),
        message=req.message,
        explanation="",
    )
    explanation = provider.explain(finding)
    return LLMExplainResponse(explanation=explanation)


# Attach API router
app.include_router(api_router)

# ── Static / Frontend Serving ────────────────────────────────────────────────

if WEB_DIST_DIR.exists() and (WEB_DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = WEB_DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(WEB_DIST_DIR / "index.html")
else:

    @app.get("/", include_in_schema=False)
    async def root_fallback():
        return {
            "name": "SecureLex IDE API",
            "status": "running",
            "version": __version__,
            "message": (
                "Backend service is operational. Frontend build not found in web/dist. "
                "Run Vite development server at http://localhost:5173 or execute 'npm run build' in web/."
            ),
            "docs_url": "/docs",
            "api_prefix": "/api",
        }
