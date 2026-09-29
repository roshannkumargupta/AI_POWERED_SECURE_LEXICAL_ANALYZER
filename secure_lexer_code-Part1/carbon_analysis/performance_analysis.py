"""
carbon_analysis/performance_analysis.py
Full performance evaluation with:
  - Precision, Recall, F1 per class
  - Confusion matrix
  - Throughput (tokens/second)
  - Latency distribution
  - WScore

Run: .venv\Scripts\python.exe -m carbon_analysis.performance_analysis
"""

import sys, os, time, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_recall_fscore_support
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from W5_6.lexer import SecureIngestionPipeline
from ML_model.hybrid_validator import HybridValidator, RuleEngine
from ML_model.ai_model import AIInferenceEngine

OUTPUT_DIR = "carbon_analysis/performance"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Ground-truth labelled test cases ─────────────────────────────
# Each entry: (source_code, list_of_expected_labels_per_token)
# We use our 5 case study inputs with known expected outputs.

TEST_CASES = [
    # (description, source, expected_label_for_flagged_tokens)
    {
        "name": "clean_code",
        "source": "def add(a, b):\n    return a + b\nresult = add(3, 7)\nprint(result)\n",
        "expected_malicious": 0,
        "expected_suspicious": 0,
    },
    {
        "name": "homoglyph",
        "source": "admin = 1\n\u0430dmin = 2\n",
        "expected_malicious": 0,
        "expected_suspicious": 1,
    },
    {
        "name": "exec_injection",
        "source": "exec(\"__import__('os').system('id')\")\n",
        "expected_malicious": 2,
        "expected_suspicious": 0,
    },
    {
        "name": "sql_injection",
        "source": "query = f\"SELECT * FROM users WHERE id = {user_id}\"\n",
        "expected_malicious": 1,
        "expected_suspicious": 0,
    },
    {
        "name": "taint_flow",
        "source": "user_input = input('cmd: ')\nos.system(user_input)\n",
        "expected_malicious": 1,
        "expected_suspicious": 2,
    },
    {
        "name": "zero_width",
        "source": "safe\u200bVar = 1\nnor\u200bmal = 2\n",
        "expected_malicious": 2,
        "expected_suspicious": 0,
    },
    {
        "name": "base64_payload",
        "source": "secret = \"SGVsbG8gd29ybGQgdGhpcyBpcyBhIHRlc3Q=\"\n",
        "expected_malicious": 0,
        "expected_suspicious": 1,
    },
    {
        "name": "shell_injection",
        "source": "cmd = \"rm -rf /\"\nos.system(cmd)\n",
        "expected_malicious": 1,
        "expected_suspicious": 1,
    },
]

LABEL_MAP = {"SAFE": 0, "SUSPICIOUS": 1, "MALICIOUS": 2}
CLASS_NAMES = ["SAFE", "SUSPICIOUS", "MALICIOUS"]


def run_pipeline(source, filename, validator, pipeline):
    """Returns (predictions_list, elapsed_ms, token_count)."""
    t0     = time.perf_counter()
    result = pipeline.process_string(source, filename)
    tokens = result.tokens
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if not tokens:
        return [], elapsed_ms, 0

    val  = validator.validate(tokens)
    exps = val["explanations"]
    preds = [LABEL_MAP.get(e["label"], 0) for e in exps]
    return preds, elapsed_ms, len(tokens)


def compute_metrics(all_true, all_pred):
    """Compute full classification metrics."""
    p, r, f1, support = precision_recall_fscore_support(
        all_true, all_pred, labels=[0,1,2],
        zero_division=0
    )
    cm = confusion_matrix(all_true, all_pred, labels=[0,1,2])
    report = classification_report(
        all_true, all_pred,
        target_names=CLASS_NAMES,
        zero_division=0
    )

    # WScore
    total = sum(support)
    recall_per_class = [r[c] if support[c] > 0 else 0.0 for c in range(3)]
    weights = [0.15, 0.30, 0.55]
    wscore  = sum(w * r for w, r in zip(weights, recall_per_class))

    return {
        "precision":   p.tolist(),
        "recall":      r.tolist(),
        "f1":          f1.tolist(),
        "support":     support.tolist(),
        "confusion":   cm.tolist(),
        "report":      report,
        "wscore":      round(wscore, 4),
    }


def plot_confusion_matrix(cm, title, output_path):
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
        ax=ax, linewidths=0.5
    )
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_per_class_metrics(metrics_dict, output_path):
    """Bar chart: Precision / Recall / F1 per class for all three modes."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    modes     = list(metrics_dict.keys())
    colors    = {'Static':'#1F3864', 'Dynamic':'#2E75B6', 'Pure_ML':'#C00000'}
    x         = np.arange(3)
    width     = 0.25

    for ax_idx, metric_name in enumerate(["precision", "recall", "f1"]):
        ax = axes[ax_idx]
        for i, mode in enumerate(modes):
            vals = metrics_dict[mode][metric_name]
            bars = ax.bar(x + i*width, vals, width,
                          label=mode, color=colors.get(mode,'gray'), alpha=0.85)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.01,
                        f'{val:.2f}', ha='center', va='bottom', fontsize=8)

        ax.set_xticks(x + width)
        ax.set_xticklabels(CLASS_NAMES)
        ax.set_ylim(0, 1.15)
        ax.set_ylabel(metric_name.capitalize())
        ax.set_title(f'{metric_name.capitalize()} by Class')
        ax.legend(title="Mode", fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle("Precision / Recall / F1 per Class\nStatic vs Dynamic vs Pure ML",
                 fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_wscore_comparison(metrics_dict, output_path):
    modes   = list(metrics_dict.keys())
    wscores = [metrics_dict[m]["wscore"] for m in modes]
    colors  = ['#1F3864', '#2E75B6', '#C00000']

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(modes, wscores, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, wscores):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Weighted Score (WScore)")
    ax.set_title("WScore Comparison: Static vs Dynamic vs Pure ML\n"
                 "WScore = 0.15×Recall(SAFE) + 0.30×Recall(SUSP) + 0.55×Recall(MAL)")
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_throughput(throughput_dict, output_path):
    modes  = list(throughput_dict.keys())
    values = list(throughput_dict.values())
    colors = ['#1F3864', '#2E75B6', '#C00000']

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(modes, values, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 5,
                f'{val:.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel("Throughput (tokens / second)")
    ax.set_title("Analysis Throughput by Mode")
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_latency_distribution(latency_dict, output_path):
    fig, ax = plt.subplots(figsize=(8, 5))
    colors  = {'Static':'#1F3864', 'Dynamic':'#2E75B6', 'Pure_ML':'#C00000'}
    for mode, latencies in latency_dict.items():
        ax.hist(latencies, bins=15, alpha=0.6, color=colors[mode], label=mode, density=True)
    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("Density")
    ax.set_title("Latency Distribution by Analysis Mode")
    ax.legend(title="Mode")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def main():
    pipeline    = SecureIngestionPipeline(output_dir="results", log_file="logs/perf_test.log")
    rule_engine = RuleEngine()

    ai_engine = None
    if os.path.exists("models/bilstm_model_real.pth"):
        try:
            ai_engine = AIInferenceEngine(
                model_path="models/bilstm_model_real.pth", device="cpu",
                log_file="logs/perf_inference.log")
        except Exception as e:
            print(f"Model load failed: {e}")

    validators = {
        "Static":  HybridValidator(rule_engine=rule_engine, ai_engine=None,     alpha=1.0),
        "Dynamic": HybridValidator(rule_engine=rule_engine, ai_engine=ai_engine, alpha=0.6),
        "Pure_ML": HybridValidator(rule_engine=rule_engine, ai_engine=ai_engine, alpha=0.0),
    }

    # Build pseudo ground truth from expected counts
    # We create synthetic true labels based on expected counts per test case
    metrics_dict    = {}
    throughput_dict = {}
    latency_dict    = {m: [] for m in validators}

    for mode, validator in validators.items():
        print(f"\n{'='*50}")
        print(f"Evaluating mode: {mode}")
        print(f"{'='*50}")

        all_true  = []
        all_pred  = []
        all_times = []
        total_tok = 0

        for tc in TEST_CASES:
            preds, elapsed_ms, n_tok = run_pipeline(
                tc["source"], tc["name"], validator, pipeline
            )
            all_times.append(elapsed_ms)
            total_tok += n_tok
            latency_dict[mode].append(elapsed_ms)

            # Build true labels based on expected counts
            # Tokens beyond expected flagged count are SAFE
            n_malicious  = tc["expected_malicious"]
            n_suspicious = tc["expected_suspicious"]
            n_safe       = max(n_tok - n_malicious - n_suspicious, 0)

            true_labels = (
                [2] * n_malicious +
                [1] * n_suspicious +
                [0] * n_safe
            )[:n_tok]
            while len(true_labels) < n_tok:
                true_labels.append(0)

            all_true.extend(true_labels)
            all_pred.extend(preds[:n_tok])

            print(f"  {tc['name']:20s}  tokens={n_tok:3d}  "
                  f"time={elapsed_ms:.1f}ms  "
                  f"pred_mal={preds.count(2) if preds else 0}  "
                  f"pred_sus={preds.count(1) if preds else 0}")

        metrics  = compute_metrics(all_true, all_pred)
        metrics_dict[mode] = metrics

        total_time_s        = sum(all_times) / 1000
        throughput          = total_tok / max(total_time_s, 1e-6)
        throughput_dict[mode] = throughput

        print(f"\n  WScore:     {metrics['wscore']}")
        print(f"  Throughput: {throughput:.0f} tokens/sec")
        print(f"\n{metrics['report']}")

        # Confusion matrix per mode
        cm = np.array(metrics['confusion'])
        plot_confusion_matrix(
            cm, f"Confusion Matrix — {mode} Mode",
            f"{OUTPUT_DIR}/confusion_matrix_{mode}.png"
        )

    # Cross-mode comparison graphs
    plot_per_class_metrics(
        metrics_dict,
        f"{OUTPUT_DIR}/per_class_metrics.png"
    )
    plot_wscore_comparison(
        metrics_dict,
        f"{OUTPUT_DIR}/wscore_comparison.png"
    )
    plot_throughput(
        throughput_dict,
        f"{OUTPUT_DIR}/throughput.png"
    )
    plot_latency_distribution(
        latency_dict,
        f"{OUTPUT_DIR}/latency_distribution.png"
    )

    # Save numeric results
    summary = {}
    for mode in validators:
        m = metrics_dict[mode]
        summary[mode] = {
            "wscore":     m["wscore"],
            "throughput": throughput_dict[mode],
            "precision":  {CLASS_NAMES[i]: round(m["precision"][i], 4) for i in range(3)},
            "recall":     {CLASS_NAMES[i]: round(m["recall"][i], 4) for i in range(3)},
            "f1":         {CLASS_NAMES[i]: round(m["f1"][i], 4) for i in range(3)},
        }
    with open(f"{OUTPUT_DIR}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary JSON: {OUTPUT_DIR}/summary.json")
    print(f"All graphs:   {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()