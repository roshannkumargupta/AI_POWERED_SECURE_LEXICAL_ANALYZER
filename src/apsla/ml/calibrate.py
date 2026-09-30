"""Temperature scaling and probability calibration for multi-class ML models."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def apply_temperature_scaling(probs: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Applies temperature scaling to class probabilities.

    Args:
        probs: (N, C) probability matrix.
        temperature: Scalar temperature T > 0 (T=1.0 is identity).

    Returns:
        Calibrated (N, C) probability matrix summing to 1.0 per row.
    """
    if temperature <= 0.0:
        temperature = 1.0
    if temperature == 1.0:
        return probs

    eps = 1e-12
    clipped = np.clip(probs, eps, 1.0)
    logits = np.log(clipped) / temperature
    exp_l = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    calibrated = exp_l / np.sum(exp_l, axis=1, keepdims=True)
    return calibrated.astype(np.float32)


def fit_temperature(probs: np.ndarray, y_true: np.ndarray) -> float:
    """Optimizes temperature T on validation probabilities to minimize cross-entropy loss.

    Args:
        probs: (N, 3) validation probabilities.
        y_true: (N,) true integer class labels (0, 1, 2).

    Returns:
        Optimal temperature T float value (bounded between 0.2 and 5.0).
    """
    eps = 1e-12
    clipped = np.clip(probs, eps, 1.0)
    base_logits = np.log(clipped)

    def nll_objective(T_arr: np.ndarray) -> float:
        T = float(T_arr[0])
        scaled_logits = base_logits / T
        exp_l = np.exp(scaled_logits - np.max(scaled_logits, axis=1, keepdims=True))
        p = exp_l / np.sum(exp_l, axis=1, keepdims=True)
        # Gather probabilities of true classes
        n_samples = len(y_true)
        true_probs = p[np.arange(n_samples), y_true]
        return float(-np.mean(np.log(np.clip(true_probs, eps, 1.0))))

    res = minimize(nll_objective, x0=[1.0], bounds=[(0.2, 5.0)], method="L-BFGS-B")
    if res.success and len(res.x) > 0:
        return float(res.x[0])
    return 1.0
