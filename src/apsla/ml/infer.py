"""Machine learning runtime inference engine with strict feature-schema verification."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Final

import numpy as np

from apsla.lexing.token import Token
from apsla.ml.features import FEATURE_SCHEMA_HASH, extract_file_features
from apsla.ml.models import UnifiedModelWrapper
from apsla.ml.windows import build_token_windows

logger = logging.getLogger("apsla.ml.infer")
ARTIFACTS_DIR: Final[Path] = Path(__file__).resolve().parent / "artifacts"
SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = ("python", "java", "javascript", "cpp")

_MODEL_CACHE: dict[
    tuple[str, float],
    tuple[UnifiedModelWrapper, dict[str, Any], str, float, float],
] = {}


class MLInferenceEngine:
    """Runtime ML inference engine with zero silent fallbacks.

    Policy:
    If model weights are missing, corrupt, or if the feature-schema SHA-256 hash
    does not exactly match FEATURE_SCHEMA_HASH, ML mode is set to 'off'.
    Random uninitialized fallbacks are strictly prohibited.
    """

    def __init__(self, model_id: str | None = None, language: str = "python") -> None:
        self.model_id: str | None = model_id
        self.language: str = language.lower() if language else "python"
        self.model_wrapper: UnifiedModelWrapper | None = None
        self.meta: dict[str, Any] = {}
        self.temperature: float = 1.0
        self.threshold_malicious: float = 0.5
        self._available: bool = False
        self._load_artifact()

    def _supports_language(self, meta: dict[str, Any], lang: str) -> bool:
        """Determines if the artifact metadata declares support for the target language."""
        if lang not in SUPPORTED_LANGUAGES and lang not in ("py", "js", "c++"):
            return False
        cand_lang = str(meta.get("language", "")).lower()
        if cand_lang == lang:
            return True
        supp = [str(x).lower() for x in meta.get("supported_languages", [])]
        if lang in supp:
            return True
        if cand_lang == "all" and lang in SUPPORTED_LANGUAGES:
            return True
        if not cand_lang and not supp and lang == "python":
            return True
        return False

    def _find_active_artifact_dir(self) -> Path | None:
        if self.model_id:
            custom_dir = ARTIFACTS_DIR / self.model_id
            if custom_dir.exists() and (custom_dir / "meta.json").exists():
                try:
                    with open(custom_dir / "meta.json", encoding="utf-8") as f:
                        meta = json.load(f)
                    if self._supports_language(meta, self.language):
                        return custom_dir
                except Exception:
                    pass
            return None

        # Look for latest or best model artifact in artifacts directory
        if not ARTIFACTS_DIR.exists():
            return None

        candidates: list[tuple[float, Path]] = []
        for d in ARTIFACTS_DIR.iterdir():
            if not d.is_dir() or d.name.startswith("test_") or d.name.startswith("tmp_"):
                continue
            meta_file = d / "meta.json"
            if not meta_file.exists():
                continue
            try:
                with open(meta_file, encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("feature_schema_hash") != FEATURE_SCHEMA_HASH:
                    continue
                if self._supports_language(meta, self.language):
                    mtime = meta_file.stat().st_mtime
                    candidates.append((mtime, d))
            except Exception:
                continue

        if not candidates:
            return None

        # Sort by modification time descending
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return candidates[0][1]

    def _load_artifact(self) -> None:
        artifact_dir = self._find_active_artifact_dir()
        if artifact_dir is None:
            logger.info(
                "No valid ML model artifact found for '%s' in %s; ML mode is 'off'",
                self.language,
                ARTIFACTS_DIR,
            )
            self._available = False
            return

        meta_file = artifact_dir / "meta.json"
        if not meta_file.exists():
            self._available = False
            return

        cache_key = (str(artifact_dir.resolve()), meta_file.stat().st_mtime)
        if cache_key in _MODEL_CACHE:
            (
                cached_wrapper,
                cached_meta,
                cached_id,
                cached_temp,
                cached_tau,
            ) = _MODEL_CACHE[cache_key]
            self.model_wrapper = cached_wrapper
            self.meta = cached_meta
            self.model_id = cached_id
            self.temperature = cached_temp
            self.threshold_malicious = cached_tau
            self._available = True
            return

        try:
            with open(meta_file, encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as exc:
            logger.warning(
                "Failed to parse ML meta.json in %s: %s; ML mode is 'off'", artifact_dir, exc
            )
            self._available = False
            return

        # Verify exact feature schema hash match (NO SILENT FALLBACK)
        stored_hash = meta.get("feature_schema_hash")
        if stored_hash != FEATURE_SCHEMA_HASH:
            logger.warning(
                "Feature schema hash mismatch in artifact %s (stored: %s, runtime: %s); ML mode is 'off'",
                artifact_dir.name,
                stored_hash,
                FEATURE_SCHEMA_HASH,
            )
            self._available = False
            return

        model_type = meta.get("model_type")
        if not model_type:
            self._available = False
            return

        try:
            wrapper = UnifiedModelWrapper(model_type=model_type, seed=meta.get("seed", 42))
            model_file = (
                artifact_dir / "model.pt"
                if model_type == "windowed_bilstm"
                else artifact_dir / "model.joblib"
            )
            if not model_file.exists():
                logger.warning("Model file %s does not exist; ML mode is 'off'", model_file)
                self._available = False
                return

            use_lang_features = bool(meta.get("use_lang_features", False))
            wrapper.load(model_file, use_lang_features=use_lang_features)
            self.model_wrapper = wrapper
            self.meta = meta
            self.model_id = meta.get("model_id", artifact_dir.name)
            self.temperature = float(meta.get("temperature", 1.0))
            self.threshold_malicious = float(meta.get("thresholds", {}).get("tau_malicious", 0.5))
            self._available = True
            _MODEL_CACHE[cache_key] = (
                self.model_wrapper,
                self.meta,
                self.model_id,
                self.temperature,
                self.threshold_malicious,
            )
            logger.info(
                "ML inference engine loaded successfully: model_id=%s, type=%s, lang=%s",
                self.model_id,
                model_type,
                self.language,
            )
        except Exception as exc:
            logger.warning("Failed to load model weights: %s; ML mode is 'off'", exc)
            self._available = False

    def is_available(self, language: str | None = None) -> bool:
        """Returns True if a validated model is loaded and ready for inference for the given language."""
        if language is None or language.lower() == self.language:
            return self._available
        if self._available and self._supports_language(self.meta, language.lower()):
            return True
        sub = MLInferenceEngine(model_id=self.model_id, language=language)
        return sub.is_available()

    def get_mode(self, language: str | None = None) -> str:
        """Returns 'on' if ML inference is active, otherwise 'off'."""
        return "on" if self.is_available(language) else "off"

    def get_model_id(self, language: str | None = None) -> str:
        """Returns the active model identifier or 'none'."""
        if language is None or language.lower() == self.language:
            return self.model_id if self._available and self.model_id else "none"
        sub = MLInferenceEngine(model_id=self.model_id, language=language)
        return sub.get_model_id()

    def predict_token_probabilities(
        self,
        tokens: list[Token],
        language: str = "python",
    ) -> np.ndarray:
        """Predicts (N, 3) class probabilities across all tokens in document.

        Columns: [P(SAFE), P(SUSPICIOUS), P(MALICIOUS)].
        If ML mode is 'off', returns (N, 3) array with P(SAFE) = 1.0.
        """
        n_tokens = len(tokens)
        if n_tokens == 0:
            return np.empty((0, 3), dtype=np.float32)

        target_lang = language.lower()
        active_wrapper = self.model_wrapper
        temperature = self.temperature

        # If current engine does not support target language, resolve dedicated engine
        if (
            not self._available
            or active_wrapper is None
            or not self._supports_language(self.meta, target_lang)
        ):
            sub = MLInferenceEngine(model_id=self.model_id, language=target_lang)
            if not sub.is_available() or sub.model_wrapper is None:
                default_probs = np.zeros((n_tokens, 3), dtype=np.float32)
                default_probs[:, 0] = 1.0
                return default_probs
            active_wrapper = sub.model_wrapper
            temperature = sub.temperature

        features, lang_id = extract_file_features(tokens, language=target_lang)
        windows_3d, windows_flat, _, _ = build_token_windows(tokens, features)

        lang_ids = np.full((n_tokens,), fill_value=lang_id, dtype=np.int64)
        probs = active_wrapper.predict_proba(
            windows_3d, windows_flat, lang_ids=lang_ids, temperature=temperature
        )
        return probs
