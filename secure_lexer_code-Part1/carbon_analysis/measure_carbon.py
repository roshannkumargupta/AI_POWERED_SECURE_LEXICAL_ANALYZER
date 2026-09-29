"""
carbon_analysis/measure_carbon.py
Measures energy consumption and CO2 emissions for three analysis modes:
  1. Static  — Rule engine only (no ML)
  2. Dynamic — Full 6-phase pipeline (rules + BiLSTM)
  3. Pure ML — BiLSTM only (no rules)

Run: .venv\Scripts\python.exe -m carbon_analysis.measure_carbon
"""

import sys
import os
import time
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecarbon import EmissionsTracker

try:
    from W5_6.lexer import SecureIngestionPipeline
    from ML_model.hybrid_validator import HybridValidator, RuleEngine
    from ML_model.ai_model import AIInferenceEngine
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────────────
TEST_FILES = {
    50:  "carbon_test/code_50lines.py",
    80:  "carbon_test/code_80lines.py",
    100: "carbon_test/code_100lines.py",
    150: "carbon_test/code_150lines.py",
}

MODEL_PATH  = "models/bilstm_model_real.pth"
OUTPUT_DIR  = "carbon_analysis/results"
N_RUNS      = 5   # Run each combination N times for stable averages

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("carbon_analysis/emissions_logs", exist_ok=True)

# ── Load pipeline components once ────────────────────────────────
print("Loading pipeline components...")
pipeline    = SecureIngestionPipeline(output_dir="results", log_file="logs/carbon_test.log")
rule_engine = RuleEngine()

ai_engine = None
if os.path.exists(MODEL_PATH):
    try:
        ai_engine = AIInferenceEngine(model_path=MODEL_PATH, device="cpu",
                                      log_file="logs/carbon_inference.log")
        print("BiLSTM model loaded.")
    except Exception as e:
        print(f"Model load failed: {e} — Dynamic mode will use rules only")
else:
    print(f"No model at {MODEL_PATH} — Dynamic mode = Static mode")

# Validators for each mode
static_validator  = HybridValidator(rule_engine=rule_engine, ai_engine=None,   alpha=1.0)
dynamic_validator = HybridValidator(rule_engine=rule_engine, ai_engine=ai_engine, alpha=0.6)
ml_validator      = HybridValidator(rule_engine=rule_engine, ai_engine=ai_engine, alpha=0.0)


def load_source(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def run_analysis(source, filename, validator, mode_label):
    """Run one analysis pass. Returns (time_ms, token_count, flagged_count)."""
    t0     = time.perf_counter()
    result = pipeline.process_string(source, filename)
    tokens = result.tokens

    if tokens:
        val      = validator.validate(tokens)
        flagged  = val["summary"]["suspicious_count"] + val["summary"]["malicious_count"]
    else:
        flagged = 0

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return elapsed_ms, len(tokens), flagged


# ── Main measurement loop ─────────────────────────────────────────
records = []

for line_count, filepath in TEST_FILES.items():
    if not os.path.exists(filepath):
        print(f"[SKIP] {filepath} not found")
        continue

    source   = load_source(filepath)
    filename = os.path.basename(filepath)
    print(f"\n{'='*55}")
    print(f"File: {filename}  ({line_count} lines)")
    print(f"{'='*55}")

    for mode_label, validator in [
        ("Static",  static_validator),
        ("Dynamic", dynamic_validator),
        ("Pure_ML", ml_validator),
    ]:
        run_times = []
        run_tokens = []
        run_flagged = []

        tracker = EmissionsTracker(
            project_name=f"{mode_label}_{line_count}lines",
            output_dir="carbon_analysis/emissions_logs",
            log_level="error",
            save_to_file=True,
            measure_power_secs=1,
        )

        print(f"\n  Mode: {mode_label}  ({N_RUNS} runs)...")
        tracker.start()

        for run_i in range(N_RUNS):
            t_ms, n_tok, n_flag = run_analysis(
                source, f"{filename}_{mode_label}_run{run_i}", validator, mode_label
            )
            run_times.append(t_ms)
            run_tokens.append(n_tok)
            run_flagged.append(n_flag)
            print(f"    Run {run_i+1}: {t_ms:.1f}ms  tokens={n_tok}  flagged={n_flag}")

        emissions = tracker.stop()   # kg CO2eq

        avg_time   = np.mean(run_times)
        std_time   = np.std(run_times)
        avg_tokens = np.mean(run_tokens)
        avg_flagged = np.mean(run_flagged)
        emissions_g = (emissions or 0.0) * 1000   # convert kg to grams

        record = {
            "lines":          line_count,
            "mode":           mode_label,
            "avg_time_ms":    round(avg_time, 3),
            "std_time_ms":    round(std_time, 3),
            "tokens":         int(avg_tokens),
            "flagged":        int(avg_flagged),
            "emissions_g_co2": round(emissions_g, 6),
            "emissions_kg_co2": round(emissions or 0.0, 9),
        }
        records.append(record)

        print(f"  → Avg time: {avg_time:.1f}ms  "
              f"CO2: {emissions_g:.4f}g  "
              f"Flagged: {avg_flagged:.0f} tokens")

# ── Save results ──────────────────────────────────────────────────
df = pd.DataFrame(records)
csv_path = f"{OUTPUT_DIR}/carbon_results.csv"
df.to_csv(csv_path, index=False)
print(f"\n\nResults saved: {csv_path}")
print(df.to_string(index=False))