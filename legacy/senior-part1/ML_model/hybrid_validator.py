"""
Phase 5 + 6 — Hybrid Validator with Taint-lite + Explainability
================================================================
Phase 5: Dangerous API detection + taint-lite tracking
Phase 6: Dual analysis (original + recovered), explainability output,
         confidence calibration
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

# Safe console output on Windows
import io
_safe_stream = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
)

try:
    from ML_model.ai_model import _safe
except ImportError:
    from ai_model import _safe


# ─────────────────────────────────────────────────────────────────
# PHASE 5: TAINT-LITE TRACKER
# ─────────────────────────────────────────────────────────────────

# Dangerous APIs that act as SINKS (if tainted data reaches these -> MALICIOUS)
_SINK_APIS = frozenset({
    "system", "exec", "eval", "compile", "popen", "check_call",
    "check_output", "Popen", "call", "run",
    "cursor.execute", "execute",
    "pickle.loads", "marshal.loads", "loads",
})

# Source functions that introduce tainted values
_SOURCE_FUNCS = frozenset({
    "input", "raw_input", "request.args", "request.form",
    "request.get", "request.json", "sys.argv",
    "os.environ", "environ.get",
})


class TaintTracker:
    """
    Simplified taint tracking across a token stream.
    Does NOT do full data-flow analysis — just tracks assignment patterns.

    Rules:
      1. If a variable is assigned the result of a SOURCE function -> tainted
      2. If a tainted variable is used as an argument to a SINK -> MALICIOUS
    """

    def __init__(self):
        self._tainted: Set[str] = set()   # set of tainted variable names
        self._log: List[str]    = []

    def reset(self):
        self._tainted.clear()
        self._log.clear()

    @property
    def tainted_vars(self) -> Set[str]:
        return frozenset(self._tainted)

    def process_stream(self, tokens: List) -> List[Dict]:
        """
        Walk the token stream and return taint-analysis annotations.
        Each annotation: {"token_index": i, "taint": "NONE"|"SOURCE"|"PROPAGATED"|"SINK"}
        """
        self.reset()
        annotations = [{"token_index": i, "taint": "NONE"} for i in range(len(tokens))]
        raw_vals    = [t.raw_value for t in tokens]

        for i, tok in enumerate(tokens):
            val = tok.raw_value

            # ── SOURCE detection ──────────────────────────────────
            # Pattern: <identifier> = input(  OR  = request.xxx
            if val in _SOURCE_FUNCS:
                annotations[i]["taint"] = "SOURCE"
                # Look backward for the variable being assigned
                var_name = self._find_lhs_var(raw_vals, i)
                if var_name:
                    self._tainted.add(var_name)
                    self._log.append(f"TAINT SOURCE: '{var_name}' ← {val}()")

            # ── PROPAGATION detection ─────────────────────────────
            # If a tainted variable appears in an expression and is assigned
            if val in self._tainted:
                annotations[i]["taint"] = "PROPAGATED"
                # Propagate to lhs if this is an rhs
                lhs = self._find_lhs_var(raw_vals, i)
                if lhs and lhs != val:
                    self._tainted.add(lhs)
                    self._log.append(f"TAINT PROPAGATED: '{lhs}' ← '{val}'")

            # ── SINK detection ────────────────────────────────────
            if val in _SINK_APIS:
                # Check if any argument in the next few tokens is tainted
                window = raw_vals[i+1 : i+10]
                for w_val in window:
                    if w_val in self._tainted:
                        annotations[i]["taint"] = "SINK"
                        annotations[i]["tainted_arg"] = w_val
                        self._log.append(
                            f"TAINT SINK: {val}(... '{w_val}' ...) — MALICIOUS"
                        )
                        break

        return annotations

    @staticmethod
    def _find_lhs_var(raw_vals: List[str], rhs_index: int) -> Optional[str]:
        """
        Look backward from rhs_index for pattern: <identifier> =
        """
        # Walk back up to 5 tokens
        for j in range(max(0, rhs_index - 5), rhs_index):
            if raw_vals[j] == "=" and j > 0:
                candidate = raw_vals[j - 1]
                if candidate.isidentifier():
                    return candidate
        return None


# ─────────────────────────────────────────────────────────────────
# RULE ENGINE  (used by HybridValidator)
# ─────────────────────────────────────────────────────────────────

class RuleEngine:
    """
    Rule-based token classifier.
    Converts SecureToken security metadata into class + confidence.
    """

    def get_rule_predictions(self, tokens: List) -> List[Dict]:
        results = []
        for tok in tokens:
            cls, conf, reasons = self._classify(tok)
            results.append({
                "class":      cls,
                "class_name": ["SAFE", "SUSPICIOUS", "MALICIOUS"][cls],
                "confidence": conf,
                "reasons":    reasons,
            })
        return results

    def _classify(self, tok) -> Tuple[int, float, List[str]]:
        reasons = []
        score   = 0.0

        DIRECT_MALICIOUS = {"exec", "eval", "__import__", "compile",
                            "pickle", "marshal", "subprocess"}
        if tok.raw_value.lower() in DIRECT_MALICIOUS:
            score += 0.55
            reasons.append(f"dangerous built-in: {tok.raw_value}")

        if tok.unicode:
            if tok.unicode.zero_width_count > 0:
                score += 0.55; reasons.append("zero-width chars")
            if tok.unicode.homoglyph_count > 0:
                score += 0.30; reasons.append(f"homoglyphs: {tok.unicode.homoglyph_count}")
            if tok.unicode.has_mixed_scripts:
                score += 0.20; reasons.append(f"mixed scripts: {tok.unicode.scripts_present}")
            if not tok.unicode.is_pure_ascii:
                score += 0.10; reasons.append("non-ASCII")

        if tok.entropy and tok.entropy.char_entropy > 4.2:
            threshold = 3.8 if tok.token_type.name == "STRING" else 4.2
            if tok.entropy.char_entropy > threshold:
                score += 0.25
                reasons.append(f"high entropy: {tok.entropy.char_entropy:.2f}")

        if tok.context:
            if tok.context.precedes_exec_or_eval:
                score += 0.55; reasons.append("near exec/eval")
            if tok.context.matches_sql_pattern:
                score += 0.25; reasons.append("SQL keyword")
            if tok.context.matches_shell_pattern:
                score += 0.35; reasons.append("shell pattern")
            if tok.context.has_base64_pattern:
                score += 0.35; reasons.append("base64 pattern")
            raw = tok.raw_value.strip('"\'')
            if len(raw) >= 12 and re.fullmatch(r'[A-Za-z0-9+/]+=*', raw):
                score += 0.30
                reasons.append("high-entropy alphanumeric string (possible encoded payload)")
            if tok.context.is_builtin_shadow:
                score += 0.20; reasons.append("shadows builtin")

        if tok.token_type.name == "STRING":

            SQL_RX = re.compile(
             r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b",
                re.IGNORECASE
            )
            if SQL_RX.search(tok.raw_value):
                score += 0.45
                reasons.append("SQL pattern in string")

        # Shell commands in strings
            SHELL_RX = re.compile(
                r"\b(rm\s+-rf|wget|curl|bash|chmod|nc |netcat|system)\b",
                re.IGNORECASE
            )
            if SHELL_RX.search(tok.raw_value):
                score += 0.45
                reasons.append("shell pattern in string")

        score = min(score, 1.0)

        if score >= 0.70:
            return 2, score, reasons   # MALICIOUS
        elif score >= 0.40:
            return 1, score, reasons   # SUSPICIOUS
        else:
            return 0, max(1.0 - score, 0.6), reasons   # SAFE


# ─────────────────────────────────────────────────────────────────
# PHASE 6: EXPLAINABILITY OUTPUT
# ─────────────────────────────────────────────────────────────────

def build_explanation(token, hybrid_result: Dict, taint_annotation: Dict) -> Dict:
    """
    Build Phase 6 explainability output for a single token.

    Returns:
        {
          "token":     original raw value,
          "recovered": recovered string,
          "label":     "SAFE" | "SUSPICIOUS" | "MALICIOUS",
          "score":     float,
          "reasons":   [list of human-readable explanations],
        }
    """
    reasons = list(hybrid_result.get("reasons", []))

    # Add recovery-derived reasons
    if hybrid_result.get("recovery_changed"):
        reasons.append(
            f"Unicode obfuscation detected (recovery changed token: "
            f"'{_safe(token.raw_value)}' -> '{_safe(hybrid_result.get('recovered',''))}')"
        )

    # Add taint reasons
    taint = taint_annotation.get("taint", "NONE")
    if taint == "SOURCE":
        reasons.append("taint: value from user-controlled source")
    elif taint == "PROPAGATED":
        reasons.append("taint: propagated from user input")
    elif taint == "SINK":
        reasons.append(
            f"taint: user-controlled data reaches sink "
            f"(arg: '{taint_annotation.get('tainted_arg', '?')}')"
        )

    # Add unicode reasons
    if token.unicode:
        if token.unicode.zero_width_count > 0:
            reasons.append(f"zero-width chars: {token.unicode.zero_width_count}")
        if token.unicode.homoglyph_count > 0:
            reasons.append(f"homoglyph chars: {token.unicode.homoglyph_count}")
        if token.unicode.has_mixed_scripts:
            reasons.append(f"mixed scripts: {token.unicode.scripts_present}")

    # Add entropy reasons
    if token.entropy and token.entropy.char_entropy > 3.5:
        reasons.append(f"high entropy: {token.entropy.char_entropy:.3f}")

    # Deduplicate while preserving order
    seen = set(); unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r); unique_reasons.append(r)

    return {
        "token":     token.raw_value,
        "recovered": hybrid_result.get("recovered", token.raw_value),
        "label":     hybrid_result.get("hybrid_class", "SAFE"),
        "score":     round(hybrid_result.get("hybrid_score", 0.0), 4),
        "reasons":   unique_reasons,
    }


# ─────────────────────────────────────────────────────────────────
# HYBRID VALIDATOR  (full Phase 5 + 6 version)
# ─────────────────────────────────────────────────────────────────

class HybridValidator:
    """
    Combines rule-based + ML predictions with taint tracking and
    explainability output.
    """

    def __init__(
        self,
        rule_engine=None,
        ai_engine=None,
        alpha:    float = 0.6,
        log_file: str   = "logs/hybrid_validator.log",
    ):
        self.rule_engine  = rule_engine or RuleEngine()
        self.ai_engine    = ai_engine
        self.alpha        = alpha
        self.taint        = TaintTracker()

        self.log = logging.getLogger("HybridValidator")
        if not self.log.handlers:
            if log_file:
                import os
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                h = logging.FileHandler(log_file, encoding="utf-8")
                h.setFormatter(logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
                ))
                self.log.addHandler(h)
            ch = logging.StreamHandler(_safe_stream)
            ch.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            ))
            self.log.addHandler(ch)
            self.log.setLevel(logging.INFO)

    # ── Main entry point ──────────────────────────────────────────

    def validate(self, tokens: List) -> Dict:
        """
        Full hybrid validation pipeline.

        Returns dict with:
          predictions: List[Dict]  — per-token results
          explanations: List[Dict] — per-token explanations (Phase 6)
          taint_log: List[str]     — taint-analysis log
          summary: Dict
        """
        self.log.info(f"Validating {len(tokens)} tokens")

        # ── Phase 5: Taint analysis ───────────────────────────────
        taint_annotations = self.taint.process_stream(tokens)

        # ── Rule predictions ──────────────────────────────────────
        rule_preds = self.rule_engine.get_rule_predictions(tokens)

        # ── AI predictions ────────────────────────────────────────
        if self.ai_engine:
            ai_preds = self.ai_engine.predict(tokens, return_probabilities=True)
        else:
            # No AI engine — fall back to rule-only predictions
            ai_preds = [
                {
                    "token_value": t.raw_value,
                    "class": r["class"],
                    "class_name": r["class_name"],
                    "confidence": r["confidence"],
                    "probabilities": self._class_to_probs(r["class"], r["confidence"]).tolist(),
                    "recovered": t.raw_value,
                    "recovery_changed": False,
                    "recovery_log": [],
                }
                for t, r in zip(tokens, rule_preds)
            ]

        # ── Combine ───────────────────────────────────────────────
        hybrid_results = []
        explanations   = []

        for i, (rule, ai) in enumerate(zip(rule_preds, ai_preds)):
            final_class, final_conf, hybrid_probs = self._combine(
                rule, ai, tokens[i], taint_annotations[i]
            )

            result = {
                "token_value":      tokens[i].raw_value,
                "token_index":      i,
                "entropy":          getattr(tokens[i].entropy, "char_entropy", None),
                "unicode_risk":     tokens[i].unicode.risk_level() if tokens[i].unicode else "LOW",
                "rule_class":       rule["class_name"],
                "rule_confidence":  rule["confidence"],
                "ai_class":         ai["class_name"],
                "ai_confidence":    ai["confidence"],
                "hybrid_class":     ["SAFE", "SUSPICIOUS", "MALICIOUS"][final_class],
                "hybrid_score":     round(final_conf, 4),
                "hybrid_probabilities": hybrid_probs.tolist(),
                "reasons":          rule.get("reasons", []),
                "recovered":        ai.get("recovered", tokens[i].raw_value),
                "recovery_changed": ai.get("recovery_changed", False),
                "taint":            taint_annotations[i]["taint"],
            }

            if final_class > 0:
                self.log.warning(
                    f"Token '{_safe(tokens[i].raw_value)}' -> "
                    f"{result['hybrid_class']} (score={final_conf:.3f})"
                )

            hybrid_results.append(result)

            # ── Phase 6: Explainability ──────────────────────────
            explanation = build_explanation(tokens[i], result, taint_annotations[i])
            explanations.append(explanation)

        return {
            "predictions":  hybrid_results,
            "explanations": explanations,
            "taint_log":    self.taint._log,
            "summary":      self._compute_summary(hybrid_results),
        }

    # ── Combination logic ─────────────────────────────────────────

    def _combine(
        self,
        rule:         Dict,
        ai:           Dict,
        token,
        taint_ann:    Dict,
    ) -> Tuple[int, float, np.ndarray]:

        rule_probs   = self._class_to_probs(rule["class"], rule["confidence"])
        ai_probs     = np.array(ai.get("probabilities",
                         self._class_to_probs(ai["class"], ai["confidence"]).tolist()),
                         dtype=np.float32)

        hybrid_probs = self.alpha * rule_probs + (1 - self.alpha) * ai_probs
        final_class  = int(np.argmax(hybrid_probs))
        final_conf   = float(hybrid_probs[final_class])

        # ── Unicode override ──────────────────────────────────────
        if token.unicode:
            risk = token.unicode.risk_level()
            if risk == "HIGH":
                if token.unicode.zero_width_count > 0 and final_class < 2:
                    final_class = 2; final_conf = 0.90
                elif final_class == 0:
                    final_class = 1; final_conf = 0.70

        # ── Entropy override ──────────────────────────────────────
        entropy = getattr(token.entropy, "char_entropy", 0)
        if entropy > 4.5 and final_class == 0:
            final_class = 1; final_conf = 0.65

        # ── Taint override ────────────────────────────────────────
        if taint_ann.get("taint") == "SINK" and final_class < 2:
            final_class = 2; final_conf = 0.92

        if taint_ann.get("taint") in ("SOURCE", "PROPAGATED") and final_class == 0:
            final_class = 1; final_conf = 0.65

        # ── Rule–AI disagreement protection ──────────────────────
        if rule["class_name"] == "MALICIOUS" and rule["confidence"] > 0.8:
            if final_class == 0:
                final_class = 1; final_conf = 0.65
                self.log.warning(
                    f"Disagreement escalation: rule=MALICIOUS->hybrid=SUSPICIOUS "
                    f"for '{_safe(token.raw_value)}'"
                )

        return final_class, final_conf, hybrid_probs

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _class_to_probs(class_idx: int, conf: float) -> np.ndarray:
        probs = np.zeros(3, dtype=np.float32)
        probs[class_idx] = conf
        remaining = (1.0 - conf) / 2.0
        for i in range(3):
            if i != class_idx:
                probs[i] = remaining
        return probs

    @staticmethod
    def _compute_summary(results: List[Dict]) -> Dict:
        counts = {"SAFE": 0, "SUSPICIOUS": 0, "MALICIOUS": 0}
        for r in results:
            counts[r["hybrid_class"]] += 1
        return {
            "total_tokens":     len(results),
            "safe_count":       counts["SAFE"],
            "suspicious_count": counts["SUSPICIOUS"],
            "malicious_count":  counts["MALICIOUS"],
        }
