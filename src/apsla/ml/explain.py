"""Feature-group occlusion explainability engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from apsla.ml.models import UnifiedModelWrapper

FEATURE_GROUPS: Final[dict[str, list[int]]] = {
    "unicode": [4, 5, 6, 7, 8, 9],
    "entropy": [10, 11, 12, 13],
    "statistical": [14, 15, 16, 17, 18],
    "recovery": [19, 20, 21, 22],
    "payload": [23, 24, 25],
    "api_keyword": [26, 27, 28, 29, 30],
    "context": [31, 32, 33, 34, 35],
    "enclosing_call": [36, 37, 38],
    "neighbours": [39, 40, 41],
    "structure": [0, 1, 2, 3, 42, 43, 44],
}


def explain_token_prediction(
    model_wrapper: UnifiedModelWrapper,
    window_3d: np.ndarray,  # (1, 9, 45)
    window_flat: np.ndarray,  # (1, 405)
    target_class: int = 2,  # 0: SAFE, 1: SUSPICIOUS, 2: MALICIOUS
    lang_id: int = 0,
    temperature: float = 1.0,
) -> dict[str, float]:
    """Computes feature-group occlusion importance for a single token window.

    Zeroes out each feature group across the window and measures the drop in
    predicted probability for `target_class`:
        Drop = P_baseline(target_class) - P_occluded(target_class)
    A higher positive drop indicates that the feature group strongly contributed
    to elevating the target class probability.

    Args:
        model_wrapper: Active trained UnifiedModelWrapper.
        window_3d: (1, 9, 45) array for the target token.
        window_flat: (1, 405) array for the target token.
        target_class: Target class index (default: 2 = MALICIOUS).
        lang_id: Integer language ID.
        temperature: Calibrated temperature scaling parameter.

    Returns:
        Mapping of feature group name to probability drop delta (float).
    """
    lang_arr = np.array([lang_id], dtype=np.int64)

    base_probs = model_wrapper.predict_proba(
        window_3d, window_flat, lang_ids=lang_arr, temperature=temperature
    )
    base_target_prob = float(base_probs[0, target_class])

    occlusion_drops: dict[str, float] = {}

    for group_name, feat_indices in FEATURE_GROUPS.items():
        occ_3d = window_3d.copy()
        occ_flat = window_flat.copy()

        # Zero out group features across all timesteps in the window
        occ_3d[:, :, feat_indices] = 0.0

        for t in range(9):
            offset = t * 45
            for f_idx in feat_indices:
                occ_flat[:, offset + f_idx] = 0.0

        occ_probs = model_wrapper.predict_proba(
            occ_3d, occ_flat, lang_ids=lang_arr, temperature=temperature
        )
        occ_target_prob = float(occ_probs[0, target_class])

        drop = base_target_prob - occ_target_prob
        occlusion_drops[group_name] = round(drop, 5)

    return occlusion_drops
