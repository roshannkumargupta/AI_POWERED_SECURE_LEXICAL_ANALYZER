"""Global configuration constants, thresholds, weights, and scoring settings."""

from __future__ import annotations

from typing import Final

from apsla.models import Severity

# ── Health Score Scoring Weights and Caps ─────────────────────────
# Score = max(0, 100 - sum(weight * min(count, cap)))
SEVERITY_WEIGHTS: Final[dict[Severity, int]] = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 12,
    Severity.MEDIUM: 5,
    Severity.LOW: 2,
    Severity.INFO: 0,
}

SEVERITY_CAPS: Final[dict[Severity, int]] = {
    Severity.CRITICAL: 4,  # Max penalty: 100
    Severity.HIGH: 6,  # Max penalty: 72
    Severity.MEDIUM: 8,  # Max penalty: 40
    Severity.LOW: 10,  # Max penalty: 20
    Severity.INFO: 0,
}

BASE_HEALTH_SCORE: Final[int] = 100

# ── Fusion Engine Weights & Boosts ────────────────────────────────
# When ML is enabled: confidence = RULE_WEIGHT * rule_conf + ML_WEIGHT * ml_p
RULE_WEIGHT: Final[float] = 0.7
ML_WEIGHT: Final[float] = 0.3

# Taint analysis boost when source-to-sink reachability is confirmed
TAINT_CONFIDENCE_BONUS: Final[float] = 0.15

# Threshold below which a rule with no taint confirmation is downgraded 1 level
NOISY_RULE_ML_THRESHOLD: Final[float] = 0.15

# Maximum allowed ML-only findings (APS-ALL-ML-001) per analysis
ML_ONLY_FINDINGS_CAP: Final[int] = 10

# ── Machine Learning Settings ─────────────────────────────────────
# Sliding window size of tokens around target token for context modeling
WINDOW_SIZE: Final[int] = 9
FEATURE_DIM: Final[int] = 45

# ── Execution Limits & Timeouts ───────────────────────────────────
# Deterministic random seed
RANDOM_SEED: Final[int] = 42

# Maximum source file size allowed for analysis (512 KB)
MAX_FILE_SIZE_BYTES: Final[int] = 512 * 1024

# Timeouts in seconds
ANALYSIS_TIMEOUT_SECONDS: Final[float] = 30.0
FIX_TIMEOUT_SECONDS: Final[float] = 10.0
TAINT_TIMEOUT_SECONDS: Final[float] = 10.0
ML_TIMEOUT_SECONDS: Final[float] = 5.0

# Aliases for specification naming conventions
HEALTH_SCORE_BASE: Final[int] = BASE_HEALTH_SCORE
FUSION_WEIGHT_RULE: Final[float] = RULE_WEIGHT
FUSION_WEIGHT_ML: Final[float] = ML_WEIGHT
TAINT_CONFIRMATION_BONUS: Final[float] = TAINT_CONFIDENCE_BONUS
ML_ONLY_CAP: Final[int] = ML_ONLY_FINDINGS_CAP
ML_WINDOW_SIZE: Final[int] = WINDOW_SIZE
FILE_SIZE_LIMIT_BYTES: Final[int] = MAX_FILE_SIZE_BYTES
TIMEOUT_ANALYSIS_SECONDS: Final[float] = ANALYSIS_TIMEOUT_SECONDS
TIMEOUT_FIX_SECONDS: Final[float] = FIX_TIMEOUT_SECONDS
TIMEOUT_TAINT_SECONDS: Final[float] = TAINT_TIMEOUT_SECONDS
TIMEOUT_ML_SECONDS: Final[float] = ML_TIMEOUT_SECONDS

# Maximum passes for idempotent Fix-All execution
MAX_FIX_PASSES: Final[int] = 3
