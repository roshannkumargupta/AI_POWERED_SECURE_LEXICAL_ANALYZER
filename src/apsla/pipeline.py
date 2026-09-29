"""Core analysis pipeline coordinating Unicode defense, lexing, rules, taint, and ML fusion."""

from __future__ import annotations

import time
from typing import Any

import regex

from apsla.lexing.common import OffsetMap
from apsla.models import (
    AnalysisResult,
    EngineMetadata,
    Finding,
    TokenInfo,
)
from apsla.rules.generic import evaluate_unicode_rules
from apsla.scoring import create_analysis_summary
from apsla.unicode_defense.recovery import recover_text

_WHITESPACE_TOKEN_REGEX = regex.compile(r"\S+")


class Analyzer:
    """Master static and hybrid security analyzer for SecureLex IDE."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        """Initialize the analyzer with optional configuration overrides."""
        self.options = options or {}

    def analyze(
        self,
        source: str,
        language: str = "generic",
        filename: str = "<editor>",
        options: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        """Execute end-to-end security analysis across source code text.

        Pipeline Stages:
          1. Normalization & Coordinate Indexing (strip initial BOM, construct OffsetMap)
          2. Unicode Defense & Adversarial Token Recovery
          3. Generic Unicode Rule Evaluation
          4. Lexical Analysis (whitespace placeholder for Phase 1; full lexer in Phase 2)
          5. Scoring & Summary Construction

        Args:
            source: Raw source code text.
            language: Target programming language identifier.
            filename: File name or virtual editor path.
            options: Optional per-request settings.

        Returns:
            AnalysisResult: Findings, token stream, metrics, and engine metadata.
        """
        start_time = time.perf_counter()
        opts = {**self.options, **(options or {})}

        # Stage 1: Normalization & Offset Map Construction
        # Note: If BOM (\ufeff) is present at offset 0, we track it in original coordinates
        offset_map = OffsetMap(source)

        # Stage 2: Unicode Defense Layer
        recovery = recover_text(source, offset_map)

        # Stage 3: Generic Unicode Security Rules
        findings: list[Finding] = evaluate_unicode_rules(
            raw_text=source,
            offset_map=offset_map,
            recovery=recovery,
        )

        # Stage 4: Lexical Analysis
        # TODO: Phase 2 will plug in full resilient language lexer and AST taint flow
        tokens: list[TokenInfo] = []
        for m in _WHITESPACE_TOKEN_REGEX.finditer(source):
            w_start, w_end = m.span()
            w_range = offset_map.span_to_range(w_start, w_end)
            word = m.group(0)

            # Check if this token overlaps with any finding range
            token_label = "SAFE"
            token_score = 0.0
            for f in findings:
                # Overlap check across line and column ranges
                no_overlap = (
                    f.range.end_line < w_range.start_line
                    or w_range.end_line < f.range.start_line
                    or (
                        f.range.end_line == w_range.start_line
                        and f.range.end_col <= w_range.start_col
                    )
                    or (
                        w_range.end_line == f.range.start_line
                        and w_range.end_col <= f.range.start_col
                    )
                )
                if not no_overlap:
                    if f.label.value == "MALICIOUS" or token_label == "SAFE":
                        token_label = f.label.value
                    elif f.label.value == "SUSPICIOUS" and token_label != "MALICIOUS":
                        token_label = "SUSPICIOUS"
                    token_score = max(token_score, f.confidence)

            tokens.append(
                TokenInfo(
                    token=word,
                    token_type="TOKEN",
                    range=w_range,
                    label=token_label,
                    score=token_score,
                )
            )

        # Stage 5: Summary & Security Health Score
        summary = create_analysis_summary(findings=findings, tokens=tokens)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        engine = EngineMetadata(
            ml_mode=opts.get("ml_mode", "off"),
            ml_model_id="none",
            taint="none",
            version="0.1.0",
            elapsed_ms=elapsed_ms,
        )

        return AnalysisResult(
            language=language,
            filename=filename,
            findings=findings,
            tokens=tokens,
            summary=summary,
            engine=engine,
        )
