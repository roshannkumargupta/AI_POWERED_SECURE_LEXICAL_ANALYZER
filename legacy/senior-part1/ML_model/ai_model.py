"""
ML_model/ai_model.py — BiLSTM + 45-Feature Hybrid Classifier
"""
from __future__ import annotations
import io, logging, os, sys
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn


def _safe(text: str) -> str:
    return text.encode("ascii", errors="backslashreplace").decode("ascii")

def _safe_stream_handler() -> logging.StreamHandler:
    stream = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
    )
    return logging.StreamHandler(stream)


# ── BiLSTM Classifier ─────────────────────────────────────────────
class TokenClassifier(nn.Module):
    """
    BiLSTM + 45-feature hybrid.
    Input A (x_seq):  (batch, seq_len, input_dim) or (batch, input_dim)
    Input B (x_feat): (batch, 45) hand-crafted features  [optional]
    Output: (batch, num_classes)
    """
    FEATURE_DIM = 45

    def __init__(self, input_dim=34, embed_dim=64, hidden_dim=128,
                 num_classes=3, num_layers=2, dropout=0.3, feature_dim=45):
        super().__init__()
        self.input_dim   = input_dim
        self.hidden_dim  = hidden_dim
        self.feature_dim = feature_dim

        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, embed_dim),
            nn.LayerNorm(embed_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.lstm = nn.LSTM(
            input_size=embed_dim, hidden_size=hidden_dim,
            num_layers=num_layers, batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.feature_proj = nn.Sequential(
            nn.Linear(feature_dim, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(dropout * 0.5),
        )
        combined_dim = hidden_dim * 2 + 64
        self.classifier = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(hidden_dim // 2, num_classes),
        )

    def forward(self, x_seq, x_feat=None):
        if x_seq.dim() == 2:
            x_seq = x_seq.unsqueeze(1)
        projected  = self.input_proj(x_seq)
        lstm_out, _ = self.lstm(projected)
        seq_vec    = lstm_out.mean(dim=1)
        if x_feat is None:
            x_feat = torch.zeros(x_seq.size(0), self.feature_dim,
                                 device=x_seq.device, dtype=x_seq.dtype)
        feat_vec  = self.feature_proj(x_feat)
        combined  = torch.cat([seq_vec, feat_vec], dim=1)
        return self.classifier(combined)


# ── Feature Extractor ─────────────────────────────────────────────
class TokenFeatureExtractor:
    """Produces legacy 34-dim AND rich 45-dim features per token."""

    @staticmethod
    def extract_legacy(token) -> np.ndarray:
        features = np.zeros(34, dtype=np.float32)
        raw = token.raw_value if token.raw_value else ""
        features[0] = token.token_type.value / 50.0
        length = len(raw)
        features[1] = length / 100.0
        features[2] = raw.count(" ") + 1 if raw else 0

        if token.unicode:
            total = max(token.unicode.ascii_count + token.unicode.non_ascii_count, 1)
            features[4] = token.unicode.ascii_count / total
            features[5] = token.unicode.non_ascii_count / total
            features[6] = token.unicode.zero_width_count / 10.0
            features[7] = token.unicode.homoglyph_count / 10.0
            features[8] = len(token.unicode.scripts_present) / 5.0
            features[9] = token.unicode.rtl_char_count / 10.0

        if token.entropy:
            features[10] = token.entropy.char_entropy / 5.0
            features[11] = token.entropy.bigram_entropy / 5.0
            features[12] = token.entropy.trigram_entropy / 5.0
            features[13] = token.entropy.normalised_entropy

        if token.context:
            features[14] = token.context.nesting_depth / 10.0
            features[15] = 1.0 if token.context.follows_import else 0.0
            features[16] = 1.0 if token.context.precedes_exec_or_eval else 0.0
            features[17] = 1.0 if token.context.is_dunder else 0.0
            features[18] = 1.0 if token.context.matches_sql_pattern else 0.0
            features[19] = 1.0 if token.context.matches_shell_pattern else 0.0
            features[20] = 1.0 if token.context.has_base64_pattern else 0.0
            features[21] = 1.0 if token.context.is_builtin_shadow else 0.0

        if token.security:
            features[22] = token.security.score
            features[23] = 1.0 if token.security.is_suspicious else 0.0

        if length > 0:
            features[24] = sum(c.isdigit() for c in raw) / length
            features[25] = sum(c.isupper() for c in raw) / length
            features[26] = sum(not c.isalnum() for c in raw) / length

        if token.unicode:
            features[27] = 1.0 if len(token.unicode.scripts_present) > 1 else 0.0

        try:    float(raw); features[28] = 1.0
        except: features[28] = 0.0

        suspicious_words = ["exec","eval","system","os","subprocess","base64","pickle","marshal"]
        if any(w in raw.lower() for w in suspicious_words):
            features[29] = 1.0

        return features

    @staticmethod
    def extract_rich(token, neighbor_tokens=None) -> np.ndarray:
        try:
            from ML_model.recovery_engine import extract_45_features_array
        except ImportError:
            from recovery_engine import extract_45_features_array
        return extract_45_features_array(token, neighbor_tokens)

    @classmethod
    def extract(cls, token, neighbor_tokens=None) -> Tuple[np.ndarray, np.ndarray]:
        return cls.extract_legacy(token), cls.extract_rich(token, neighbor_tokens)


# ── Inference Engine ──────────────────────────────────────────────
class AIInferenceEngine:

    def __init__(self, model_path=None, device="cpu",
                 log_file="logs/ML_model_inference.log"):
        self.device      = torch.device(device)
        self.model       = TokenClassifier().to(self.device)
        self.extractor   = TokenFeatureExtractor()
        self.class_names = ["SAFE", "SUSPICIOUS", "MALICIOUS"]

        try:
            from ML_model.recovery_engine import RecoveryEngine
        except ImportError:
            from recovery_engine import RecoveryEngine
        self._recovery = RecoveryEngine()

        self.log = logging.getLogger("AIInferenceEngine")
        if not self.log.handlers:
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
                fh.setLevel(logging.DEBUG)
                self.log.addHandler(fh)
            ch = _safe_stream_handler()
            ch.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
            ch.setLevel(logging.INFO)
            self.log.addHandler(ch)
            self.log.setLevel(logging.DEBUG)

        if model_path:
            self.load_model(model_path)
        else:
            self.log.warning("No model path — using untrained model")

    def load_model(self, path: str):
        try:
            ckpt = torch.load(path, map_location=self.device)
            if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
                self.model = TokenClassifier(
                    input_dim=ckpt.get("input_dim", 34),
                    embed_dim=ckpt.get("embed_dim", 64),
                    hidden_dim=ckpt.get("hidden_dim", 128),
                    num_classes=ckpt.get("num_classes", 3),
                    num_layers=ckpt.get("num_layers", 2),
                    feature_dim=ckpt.get("feature_dim", 45),
                ).to(self.device)
                self.model.load_state_dict(ckpt["model_state_dict"])
            else:
                self.model.load_state_dict(ckpt)
            self.model.eval()
            self.log.info(f"Loaded BiLSTM model from {path}")
        except FileNotFoundError:
            self.log.error(f"Model not found: {path}")
        except Exception as e:
            self.log.error(f"Failed to load model: {e}")

    def predict(self, tokens: List, return_probabilities=True) -> List[Dict]:
        if not tokens:
            return []
        results = []
        self.model.eval()

        with torch.no_grad():
            for i, token in enumerate(tokens):
                lo = max(0, i-2); hi = min(len(tokens), i+3)
                neighbors = [tokens[j] for j in range(lo, hi) if j != i]

                # Original token
                leg, rich = self.extractor.extract(token, neighbors)
                x_seq  = torch.from_numpy(leg).unsqueeze(0).to(self.device)
                x_feat = torch.from_numpy(rich).unsqueeze(0).to(self.device)
                logits = self.model(x_seq, x_feat)
                probs_orig = torch.softmax(logits / 1.5, dim=-1).cpu().numpy()[0]

                # Recovered token (dual analysis)
                rec = self._recovery.recover(token.raw_value)
                if rec.changed:
                    mock = self._make_mock(token, rec.recovered)
                    leg_r, rich_r = self.extractor.extract(mock, neighbors)
                    x_seq_r  = torch.from_numpy(leg_r).unsqueeze(0).to(self.device)
                    x_feat_r = torch.from_numpy(rich_r).unsqueeze(0).to(self.device)
                    logits_r = self.model(x_seq_r, x_feat_r)
                    probs_rec = torch.softmax(logits_r / 1.5, dim=-1).cpu().numpy()[0]
                    final_probs = np.maximum(probs_orig, probs_rec)
                else:
                    probs_rec   = probs_orig
                    final_probs = probs_orig

                pred_class = int(np.argmax(final_probs))
                confidence = float(final_probs[pred_class])

                result = {
                    "token_value":           token.raw_value,
                    "token_index":           i,
                    "class":                 pred_class,
                    "class_name":            self.class_names[pred_class],
                    "confidence":            confidence,
                    "recovered":             rec.recovered,
                    "recovery_changed":      rec.changed,
                    "recovery_log":          rec.log,
                }
                if return_probabilities:
                    result["probabilities"]           = final_probs.tolist()
                    result["probabilities_original"]  = probs_orig.tolist()
                    result["probabilities_recovered"] = probs_rec.tolist()

                if pred_class > 0:
                    self.log.info(
                        f"Token '{_safe(token.raw_value)}' -> "
                        f"{self.class_names[pred_class]} (conf={confidence:.3f})"
                    )
                results.append(result)
        return results

    def predict_batch(self, token_streams, batch_size=8):
        return [self.predict(stream) for stream in token_streams]

    @staticmethod
    def _make_mock(original_token, recovered_raw: str):
        from dataclasses import dataclass

        @dataclass
        class _Mock:
            raw_value:  str
            token_type: object
            line:       int
            column:     int
            unicode:    object = None
            entropy:    object = None
            context:    object = None
            security:   object = None
            length:     int    = 0

        m = _Mock(
            raw_value=recovered_raw,
            token_type=original_token.token_type,
            line=original_token.line,
            column=original_token.column,
            unicode=original_token.unicode,
            entropy=original_token.entropy,
            context=original_token.context,
            security=original_token.security,
        )
        m.length = len(recovered_raw)
        return m