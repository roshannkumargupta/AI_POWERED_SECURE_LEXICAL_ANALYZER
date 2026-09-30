"""Shared data structures and definitions for synthetic snippet generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from apsla.lexing.token import Token

LABEL_SAFE: Final[int] = 0
LABEL_SUSPICIOUS: Final[int] = 1
LABEL_MALICIOUS: Final[int] = 2

LABEL_NAMES: Final[tuple[str, ...]] = ("SAFE", "SUSPICIOUS", "MALICIOUS")
LABEL_STR_TO_INT: Final[dict[str, int]] = {
    "SAFE": LABEL_SAFE,
    "SUSPICIOUS": LABEL_SUSPICIOUS,
    "MALICIOUS": LABEL_MALICIOUS,
}
LABEL_INT_TO_STR: Final[dict[int, str]] = {
    LABEL_SAFE: "SAFE",
    LABEL_SUSPICIOUS: "SUSPICIOUS",
    LABEL_MALICIOUS: "MALICIOUS",
}


@dataclass
class SyntheticSnippet:
    """A generated code snippet with ground-truth per-token security labels."""

    snippet_id: str
    template_family: str
    language: str
    code: str
    tokens: list[Token]
    token_labels: list[int]  # 0: SAFE, 1: SUSPICIOUS, 2: MALICIOUS
    metadata: dict[str, str] = field(default_factory=dict)


def get_legacy_raw_skip_reason() -> str:
    """Explains why legacy senior CSV datasets in data/raw/ are excluded from training.

    Documentation rationale:
    The files in data/raw/ (homoglyph_attacks.csv, injection_payloads.csv, safe_tokens.csv)
    contain isolated single tokens and pre-computed features from an ad-hoc prototype.
    They do NOT contain source code documents or token sequences, making it impossible
    to construct valid 9-token sliding context windows or extract lexical and syntactic
    context. Furthermore, their labels were assigned via crude heuristics without AST
    verification. They are therefore excluded to ensure zero data pollution.
    """
    return (
        "Skipped legacy CSVs in data/raw/: files contain isolated pre-computed token rows "
        "without source documents or token context required for 9-token window modeling."
    )
