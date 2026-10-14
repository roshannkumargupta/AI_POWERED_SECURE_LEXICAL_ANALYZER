"""Regression coverage for the golden collector's API response normalization."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi import testclient


def _load_golden_script() -> ModuleType:
    script = Path(__file__).resolve().parents[2] / "scripts" / "golden.py"
    spec = importlib.util.spec_from_file_location("golden_script_under_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("samples", "expected"),
    [
        ([{"id": "sample-1", "title": "Example"}, "unexpected-entry"], [{"id": "sample-1", "title": "Example", "language": None, "category": None, "filename": None}]),
        ({"detail": "samples temporarily unavailable"}, {"detail": "samples temporarily unavailable"}),
    ],
    ids=["bug-005-mixed-sample-entries", "bug-005-non-list-error-response"],
)
def test_bug_005_golden_metadata_guards_non_dict_samples(
    monkeypatch: pytest.MonkeyPatch,
    samples: Any,
    expected: Any,
) -> None:
    class Response:
        def __init__(self, data: Any) -> None:
            self.data = data

        def json(self) -> Any:
            return self.data

    class FakeClient:
        def __init__(self, _app: Any, **_kwargs: Any) -> None:
            pass

        def get(self, path: str) -> Response:
            return Response([{"id": "python"}] if path == "/api/languages" else samples)

    monkeypatch.setattr(testclient, "TestClient", FakeClient)
    actual = _load_golden_script().collect_api_metadata()
    assert actual["samples"] == expected
