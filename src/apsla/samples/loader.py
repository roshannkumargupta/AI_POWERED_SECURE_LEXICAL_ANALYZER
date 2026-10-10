"""Load and validate sample metadata and UTF-8 source files."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from apsla.samples.schema import SampleMeta


@lru_cache(maxsize=1)
def load_samples() -> tuple[tuple[SampleMeta, str], ...]:
    """Read the manifest and validate each non-pending sample and source file."""
    root = files("apsla.samples")
    try:
        raw: Any = json.loads(root.joinpath("manifest.json").read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("manifest must be a JSON array")
        result: list[tuple[SampleMeta, str]] = []
        seen: set[str] = set()
        for row in raw:
            meta = SampleMeta.model_validate(row)
            if meta.id in seen:
                raise ValueError(f"duplicate sample id: {meta.id}")
            seen.add(meta.id)
            path = meta.file.replace("\\", "/").split("/")
            if len(path) != 2 or path[0] not in {"python", "java", "javascript", "cpp", "pending"}:
                raise ValueError(f"invalid sample path: {meta.file}")
            source = root.joinpath(*path).read_text(encoding="utf-8")
            if meta.pending_reason is None:
                result.append((meta, source))
        return tuple(result)
    except Exception as exc:
        raise RuntimeError(f"Invalid sample catalogue: {exc}") from exc


def load_sample(sample_id: str) -> tuple[SampleMeta, str] | None:
    """Return one shipped sample by ID, or None when it is unknown or pending."""
    return next(((meta, code) for meta, code in load_samples() if meta.id == sample_id), None)
