"""
run_secure_engine.py — Full Pipeline Runner
============================================
Ties together all phases:

  RAW CODE
    Phase 1: Unicode Scan (ZWS + Bidi)
    Phase 1: Normalization + Confusable Mapping
    Phase 1: Recovery Engine
    W5_6:   Tokenization (BaselineLexer)
    Phase 2: Feature Extraction (45 features)
    Phase 4: BiLSTM Sequence Model
    Phase 5: Rule Engine + Taint-lite
    Phase 6: Hybrid Decision (Original + Recovered)
    Phase 6: Explainability Output

Usage:
    python ML_model/run_secure_engine.py
    python ML_model/run_secure_engine.py --file path/to/file.py
    python ML_model/run_secure_engine.py --model models/bilstm_model_real.pth
"""

from __future__ import annotations

import argparse
import json
import os
import sys

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from W5_6.lexer import SecureIngestionPipeline
from ML_model.ai_model       import AIInferenceEngine
from ML_model.hybrid_validator import HybridValidator, RuleEngine
from ML_model.recovery_engine  import RecoveryEngine

# SAMPLE INPUTS (from roadmap doc)

SAMPLE_INPUTS = {
    "clean_code": """\
def add(a, b):
    \"\"\"Return the sum of a and b.\"\"\"
    return a + b

result = add(3, 7)
print(result)
""",

    "obfuscated_code": """\
# Cyrillic homoglyph attack
аdd = lambda х, у: х + у
exec("__import__('os').system('id')")
""",

    "high_entropy_code": """\
secret = "aGVsbG8gd29ybGQ="
key    = "x7Kp!mQ@zR#nY$vW"
""",

    "sql_injection_code": """\
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
""",

    "taint_flow_code": """\
user_input = input("Enter your name: ")
cmd = user_input
os.system(cmd)
""",

    "zero_width_code": "safe\u200bVar = 1\nnor\u200bmal = 2\n",
}


# RUNNER

def run(
    source:     str,
    filename:   str   = "<string>",
    model_path: str   = None,
    verbose:    bool  = True,
) -> dict:
    """
    Full pipeline: source code -> explainability report.
    Returns the full validation result dict.
    """

    # Phase 1: Pre-scan raw source for unicode threats 
    rec_engine = RecoveryEngine()
    threat_scan = rec_engine.scan_for_unicode_threats(source)
    if threat_scan["has_threats"]:
        print(f"\n[!] Unicode threats in source: "
              f"ZWS={threat_scan['zws_count']} "
              f"Bidi={threat_scan['bidi_count']} "
              f"Confusables={threat_scan['conf_count']}")

    #  W5_6: Tokenize + enrich 
    pipeline = SecureIngestionPipeline(output_dir="results", log_file="logs/pipeline.log")
    result   = pipeline.process_string(source, filename)

    if not result.tokens:
        print("[!] No tokens produced — check source.")
        return {}

    tokens = result.tokens

    # AI Engine
    ai_engine = None
    if model_path and os.path.exists(model_path):
        ai_engine = AIInferenceEngine(model_path=model_path, device="cpu")
    elif model_path:
        print(f"[!] Model not found at {model_path} — running rule-only mode")

    # Hybrid Validation (Phase 5 + 6)
    validator     = HybridValidator(
        rule_engine=RuleEngine(),
        ai_engine=ai_engine,
        alpha=0.6,
    )
    validation    = validator.validate(tokens)

    # Print results
    if verbose:
        _print_report(validation, threat_scan)

    return validation


def _print_report(validation: dict, threat_scan: dict):
    summary = validation["summary"]
    print("\n" + "=" * 65)
    print("HYBRID VALIDATION REPORT")
    print("=" * 65)
    print(f"Total tokens   : {summary['total_tokens']}")
    print(f"SAFE           : {summary['safe_count']}")
    print(f"SUSPICIOUS     : {summary['suspicious_count']}")
    print(f"MALICIOUS      : {summary['malicious_count']}")

    if threat_scan.get("has_threats"):
        print(f"\nUnicode threats: ZWS={threat_scan['zws_count']} "
              f"Bidi={threat_scan['bidi_count']} "
              f"Confusables={threat_scan['conf_count']}")

    # Taint log
    taint_log = validation.get("taint_log", [])
    if taint_log:
        print("\nTaint Analysis:")
        for entry in taint_log:
            print(f"  {entry}")

    # Explanations (only non-SAFE)
    explanations = validation.get("explanations", [])
    flagged      = [e for e in explanations if e["label"] != "SAFE"]

    if flagged:
        print(f"\nFlagged tokens ({len(flagged)}):")
        print("-" * 65)
        for exp in flagged:
            token_safe = exp["token"].encode("ascii", errors="backslashreplace").decode()
            rec_safe   = exp["recovered"].encode("ascii", errors="backslashreplace").decode()
            print(f"  Token    : {token_safe!r}")
            if rec_safe != token_safe:
                print(f"  Recovered: {rec_safe!r}")
            print(f"  Label    : {exp['label']}  (score={exp['score']:.3f})")
            if exp["reasons"]:
                for r in exp["reasons"]:
                    print(f"    • {r}")
            print()
    else:
        print("\n✓ No flagged tokens.")

    print("=" * 65)


# CLI ENTRY POINT

def main():
    parser = argparse.ArgumentParser(description="Secure Lexer Engine")
    parser.add_argument("--file",   type=str, default=None,
                        help="Python file to analyse")
    parser.add_argument("--sample", type=str, default=None,
                        choices=list(SAMPLE_INPUTS.keys()),
                        help="Use a built-in sample input")
    parser.add_argument("--model",  type=str,
                        default="models/bilstm_model_real.pth",
                        help="Path to trained BiLSTM checkpoint")
    parser.add_argument("--all-samples", action="store_true",
                        help="Run all built-in samples")
    parser.add_argument("--json-out", type=str, default=None,
                        help="Save full JSON report to this path")
    args = parser.parse_args()

    if args.all_samples:
        for name, code in SAMPLE_INPUTS.items():
            print(f"\n{'#'*65}")
            print(f"# SAMPLE: {name}")
            print(f"{'#'*65}")
            result = run(code, filename=name, model_path=args.model)
        return

    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        result = run(source, filename=args.file, model_path=args.model)
    elif args.sample:
        source = SAMPLE_INPUTS[args.sample]
        result = run(source, filename=args.sample, model_path=args.model)
    else:
        # Default: run all samples
        for name, code in SAMPLE_INPUTS.items():
            print(f"\n{'#'*65}")
            print(f"# SAMPLE: {name}")
            print(f"{'#'*65}")
            run(code, filename=name, model_path=args.model)
        return

    if args.json_out and result:
        with open(args.json_out, "w", encoding="utf-8") as f:
            # Make JSON-serialisable (numpy floats -> Python floats)
            def _fix(obj):
                if isinstance(obj, dict):
                    return {k: _fix(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_fix(v) for v in obj]
                if hasattr(obj, "item"):
                    return obj.item()
                return obj
            json.dump(_fix(result), f, indent=2, ensure_ascii=False)
        print(f"\nJSON report saved -> {args.json_out}")


if __name__ == "__main__":
    main()


"""

.venv\Scripts\python.exe -m ML_model.train_model

.venv\Scripts\python.exe -m ML_model.run_secure_engine --all-samples

.venv\Scripts\python.exe -m uvicorn frontend.api:app --reload --port 8000
"""