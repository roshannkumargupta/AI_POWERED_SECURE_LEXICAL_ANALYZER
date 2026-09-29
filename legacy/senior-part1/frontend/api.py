"""
frontend/api.py  —  FastAPI backend
Run: uvicorn frontend.api:app --reload --port 8000
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from W5_6.lexer import SecureIngestionPipeline
from ML_model.hybrid_validator import HybridValidator, RuleEngine
from ML_model.ai_model import AIInferenceEngine

app = FastAPI(title="Secure Lexer API")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load pipeline once at startup ─────────────────────────────
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(_ROOT_DIR, "results"), exist_ok=True)
os.makedirs(os.path.join(_ROOT_DIR, "logs"), exist_ok=True)

pipeline  = SecureIngestionPipeline(
    output_dir=os.path.join(_ROOT_DIR, "results"),
    log_file=os.path.join(_ROOT_DIR, "logs", "api.log")
)
rule_engine = RuleEngine()

# Load model if available — else rule-only mode
MODEL_PATH = os.path.join(_ROOT_DIR, "models", "bilstm_model_real.pth")
ai_engine  = None
try:
    if os.path.exists(MODEL_PATH):
        ai_engine = AIInferenceEngine(model_path=MODEL_PATH, device="cpu",
                                      log_file=os.path.join(_ROOT_DIR, "logs", "api_inference.log"))
except Exception as e:
    print(f"[WARNING] Model not loaded: {e} — running rule-only mode")

validator = HybridValidator(rule_engine=rule_engine, ai_engine=ai_engine, alpha=0.6)


# ── Request / Response models ──────────────────────────────────
class AnalyzeRequest(BaseModel):
    source: str
    filename: str = "<editor>"

class TokenResult(BaseModel):
    token:        str
    token_type:   str
    line:         int
    column:       int
    label:        str          # SAFE / SUSPICIOUS / MALICIOUS
    score:        float
    reasons:      list[str]
    recovered:    str
    entropy:      float | None

class AnalyzeResponse(BaseModel):
    filename:      str
    total_tokens:  int
    safe:          int
    suspicious:    int
    malicious:     int
    taint_log:     list[str]
    tokens:        list[TokenResult]
    error:         str | None = None


# ── Routes ─────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": ai_engine is not None}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.source.strip():
        return AnalyzeResponse(filename=req.filename, total_tokens=0,
                               safe=0, suspicious=0, malicious=0,
                               taint_log=[], tokens=[], error="Empty source")
    try:
        # Lex + enrich
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', req.filename)
        result   = pipeline.process_string(req.source, safe_filename)
        tokens   = result.tokens

        # Hybrid validation
        val      = validator.validate(tokens)
        preds    = val["predictions"]
        exps     = val["explanations"]
        taint    = val.get("taint_log", [])

        # Build token list
        token_results = []
        for tok, pred, exp in zip(tokens, preds, exps):
            token_results.append(TokenResult(
                token      = tok.raw_value,
                token_type = tok.token_type.name,
                line       = tok.line,
                column     = tok.column,
                label      = exp["label"],
                score      = exp["score"],
                reasons    = exp["reasons"],
                recovered  = exp.get("recovered", tok.raw_value),
                entropy    = round(tok.entropy.char_entropy, 3) if tok.entropy else None,
            ))

        summary = val["summary"]
        return AnalyzeResponse(
            filename     = req.filename,
            total_tokens = summary["total_tokens"],
            safe         = summary["safe_count"],
            suspicious   = summary["suspicious_count"],
            malicious    = summary["malicious_count"],
            taint_log    = taint,
            tokens       = token_results,
        )

    except Exception as e:
        import traceback
        return AnalyzeResponse(filename=req.filename, total_tokens=0,
                               safe=0, suspicious=0, malicious=0,
                               taint_log=[], tokens=[],
                               error=str(e) + "\n" + traceback.format_exc())


# Serve React frontend 
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.join(_FRONTEND_DIR, "app")

app.mount("/app", StaticFiles(directory=_APP_DIR), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(_APP_DIR, "index.html"))

@app.get("/app/App.jsx")
def serve_jsx():
    return FileResponse(os.path.join(_APP_DIR, "App.jsx"),
                        media_type="application/javascript")