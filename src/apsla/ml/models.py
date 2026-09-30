"""Model definitions: Logistic Regression, Random Forest, HistGradientBoosting, and Windowed BiLSTM."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# ── Neural Windowed BiLSTM ────────────────────────────────────────────────────


class WindowedBiLSTM(nn.Module):
    """Windowed BiLSTM over 9-token sliding windows.

    Architecture (matching PROJECT_SPEC section G):
    Linear(45->64) + LayerNorm + ReLU
    -> BiLSTM(hidden 64, 1 layer) over the window with 8-dim language embedding concatenated to each timestep
    -> Concat forward/backward state at the centre (index 4)
    -> MLP 128->64->3.
    """

    def __init__(
        self,
        feature_dim: int = 45,
        hidden_dim: int = 64,
        num_languages: int = 8,
        lang_embed_dim: int = 8,
        num_classes: int = 3,
    ) -> None:
        super().__init__()
        self.feature_dim = feature_dim
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes

        # Learned language embedding (8-dim)
        self.lang_embedding = nn.Embedding(num_languages, lang_embed_dim)

        # Input projection & normalization
        self.in_proj = nn.Linear(feature_dim, hidden_dim)
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.relu = nn.ReLU()

        # BiLSTM processing (64 forward + 64 backward = 128)
        lstm_input_dim = hidden_dim + lang_embed_dim
        self.bilstm = nn.LSTM(
            input_size=lstm_input_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )

        # Centre-state MLP classifier (128 -> 64 -> 3)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor, lang_ids: torch.Tensor | None = None) -> torch.Tensor:
        """Forward pass over (B, 9, 45) windows.

        Args:
            x: (B, 9, 45) tensor of window token features.
            lang_ids: (B,) tensor of language integer IDs (default: all 0).

        Returns:
            (B, 3) logits.
        """
        B, T, _ = x.shape
        if lang_ids is None:
            lang_ids = torch.zeros(B, dtype=torch.long, device=x.device)

        # 1. Project input tokens: Linear(45->64) + LayerNorm + ReLU
        proj = self.relu(self.layer_norm(self.in_proj(x)))  # (B, T, 64)

        # 2. Concatenate 8-dim language embedding at every timestep
        lang_emb = self.lang_embedding(lang_ids).unsqueeze(1).expand(-1, T, -1)  # (B, T, 8)
        lstm_in = torch.cat([proj, lang_emb], dim=-1)  # (B, T, 72)

        # 3. BiLSTM sequence processing
        lstm_out, _ = self.bilstm(lstm_in)  # (B, T, 128)

        # 4. Concat forward/backward state at the centre (index 4)
        center_idx = T // 2
        center_repr = lstm_out[:, center_idx, :]  # (B, 128)

        # 5. MLP 128->64->3
        logits = self.mlp(center_repr)  # (B, 3)
        return logits


# ── Model Wrapper ─────────────────────────────────────────────────────────────


class UnifiedModelWrapper:
    """Standardized wrapper exposing fit and predict_proba across all 4 architectures."""

    def __init__(self, model_type: str, seed: int = 42) -> None:
        self.model_type = model_type
        self.seed = seed
        self.model: Any = None
        self._init_model()

    def _init_model(self) -> None:
        if self.model_type == "logistic_regression":
            self.model = LogisticRegression(
                class_weight="balanced",
                max_iter=300,
                random_state=self.seed,
            )
        elif self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=14,
                class_weight="balanced",
                random_state=self.seed,
                n_jobs=1,
            )
        elif self.model_type == "hist_gradient_boosting":
            self.model = HistGradientBoostingClassifier(
                class_weight="balanced",
                max_iter=100,
                random_state=self.seed,
            )
        elif self.model_type == "windowed_bilstm":
            torch.manual_seed(self.seed)
            self.model = WindowedBiLSTM()
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")

    def fit(
        self,
        X_3d: np.ndarray,
        X_flat: np.ndarray,
        y: np.ndarray,
        lang_ids: np.ndarray | None = None,
        epochs: int = 5,
        batch_size: int = 128,
        lr: float = 1e-3,
        val_data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None,
    ) -> None:
        """Trains the underlying model."""
        if self.model_type in ("logistic_regression", "random_forest", "hist_gradient_boosting"):
            self.model.fit(X_flat, y)

        elif self.model_type == "windowed_bilstm":
            device = torch.device("cpu")
            self.model.to(device)
            self.model.train()

            # Compute class weights for imbalance
            classes, counts = np.unique(y, return_counts=True)
            total = len(y)
            n_classes = 3
            weights_arr = np.ones(n_classes, dtype=np.float32)
            for c, cnt in zip(classes, counts, strict=False):
                weights_arr[c] = total / (n_classes * cnt)
            class_weights = torch.tensor(weights_arr, dtype=torch.float32, device=device)

            criterion = nn.CrossEntropyLoss(weight=class_weights)
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)

            N = len(y)
            indices = np.arange(N)

            if lang_ids is None:
                lang_ids = np.zeros(N, dtype=np.int64)

            for epoch in range(epochs):
                np.random.shuffle(indices)
                for start_idx in range(0, N, batch_size):
                    batch_idx = indices[start_idx : start_idx + batch_size]
                    bx = torch.tensor(X_3d[batch_idx], dtype=torch.float32, device=device)
                    blang = torch.tensor(lang_ids[batch_idx], dtype=torch.long, device=device)
                    by = torch.tensor(y[batch_idx], dtype=torch.long, device=device)

                    optimizer.zero_grad()
                    logits = self.model(bx, blang)
                    loss = criterion(logits, by)
                    loss.backward()
                    optimizer.step()

    def predict_proba(
        self,
        X_3d: np.ndarray,
        X_flat: np.ndarray,
        lang_ids: np.ndarray | None = None,
        temperature: float = 1.0,
    ) -> np.ndarray:
        """Predicts calibrated class probabilities (SAFE, SUSPICIOUS, MALICIOUS)."""
        if self.model_type in ("logistic_regression", "random_forest", "hist_gradient_boosting"):
            probs = self.model.predict_proba(X_flat)
            # Ensure 3-column probability array
            if probs.shape[1] < 3:
                full_probs = np.zeros((len(X_flat), 3), dtype=np.float32)
                for i, c in enumerate(self.model.classes_):
                    full_probs[:, c] = probs[:, i]
                probs = full_probs
            # Apply temperature scaling if T != 1.0
            if temperature != 1.0:
                eps = 1e-12
                logits = np.log(np.clip(probs, eps, 1.0)) / temperature
                exp_l = np.exp(logits - np.max(logits, axis=1, keepdims=True))
                probs = exp_l / np.sum(exp_l, axis=1, keepdims=True)
            return probs.astype(np.float32)

        elif self.model_type == "windowed_bilstm":
            device = torch.device("cpu")
            self.model.to(device)
            self.model.eval()

            N = len(X_3d)
            if N == 0:
                return np.empty((0, 3), dtype=np.float32)

            if lang_ids is None:
                lang_ids = np.zeros(N, dtype=np.int64)

            batch_size = 256
            all_probs: list[np.ndarray] = []

            with torch.no_grad():
                for start_idx in range(0, N, batch_size):
                    bx = torch.tensor(
                        X_3d[start_idx : start_idx + batch_size], dtype=torch.float32, device=device
                    )
                    blang = torch.tensor(
                        lang_ids[start_idx : start_idx + batch_size],
                        dtype=torch.long,
                        device=device,
                    )
                    logits = self.model(bx, blang)
                    if temperature != 1.0:
                        logits = logits / temperature
                    probs = torch.softmax(logits, dim=-1).cpu().numpy()
                    all_probs.append(probs)

            return np.vstack(all_probs).astype(np.float32)

        raise ValueError(f"Unknown model_type: {self.model_type}")

    def predict(
        self,
        X_3d: np.ndarray,
        X_flat: np.ndarray,
        lang_ids: np.ndarray | None = None,
        threshold_malicious: float = 0.5,
    ) -> np.ndarray:
        """Predicts class labels using tuned malicious threshold tau."""
        probs = self.predict_proba(X_3d, X_flat, lang_ids)
        preds = np.argmax(probs, axis=1)

        # If malicious probability exceeds threshold, override to MALICIOUS (2)
        mal_mask = probs[:, 2] >= threshold_malicious
        preds[mal_mask] = 2
        return preds

    def save(self, target_dir: Path) -> Path:
        """Saves model weights to disk (must stay under 50 MB limit)."""
        target_dir.mkdir(parents=True, exist_ok=True)
        if self.model_type == "windowed_bilstm":
            file_path = target_dir / "model.pt"
            torch.save(self.model.state_dict(), file_path)
        else:
            file_path = target_dir / "model.joblib"
            joblib.dump(self.model, file_path)

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50.0:
            raise RuntimeError(f"Model file size ({file_size_mb:.2f} MB) exceeds 50 MB limit!")
        return file_path

    def load(self, model_file: Path) -> None:
        """Loads model weights from disk."""
        if self.model_type == "windowed_bilstm":
            self.model = WindowedBiLSTM()
            self.model.load_state_dict(torch.load(model_file, map_location=torch.device("cpu")))
            self.model.eval()
        else:
            self.model = joblib.load(model_file)
