"""Unit tests for Phase 12 Optional LLM Providers and Shadow Fix Verification.

All tests are hermetic and run offline using fake httpx.MockTransport with NO API keys or network.
"""

import json

import httpx
import pytest

from apsla.fixes.verifier import verify_fix
from apsla.llm.anthropic_provider import AnthropicProvider
from apsla.llm.gemini_provider import GeminiProvider
from apsla.llm.null import NullProvider
from apsla.llm.openai_compat import OpenAICompatProvider
from apsla.llm.provider import get_configured_llm_provider
from apsla.models import Finding, Range, Severity


def _dummy_finding(rule_id: str = "APS-PY-INJ-001", line: int = 2) -> Finding:
    return Finding(
        id="f-test-inj",
        rule_id=rule_id,
        severity=Severity.HIGH,
        confidence=0.85,
        message="Command injection risk",
        range=Range(start_line=line, start_col=1, end_line=line, end_col=20),
    )


def test_null_provider_defaults():
    """NullProvider is inactive and returns empty results."""
    provider = NullProvider()
    assert provider.name == "none"
    assert provider.is_configured() is False
    assert provider.suggest_fix("x = 1", _dummy_finding()) == []
    assert provider.explain(_dummy_finding()) == ""


def test_get_configured_llm_provider_default(monkeypatch: pytest.MonkeyPatch):
    """When no keys in env, defaults to NullProvider."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = get_configured_llm_provider()
    assert isinstance(provider, NullProvider)
    assert provider.is_configured() is False


def test_openai_compat_provider_with_mock_transport():
    """Verify OpenAICompatProvider parses valid JSON response from mock transport."""

    def mock_handler(request: httpx.Request):
        assert request.url == "https://api.openai.com/v1/chat/completions"
        assert request.headers.get("Authorization") == "Bearer sk-fake-key"
        payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Use subprocess.run with argument array",
                                "explanation": "Avoid shell=True string concatenation",
                                "replacement": "subprocess.run(['ls', arg], check=True)",
                            }
                        )
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(mock_handler)
    provider = OpenAICompatProvider(api_key="sk-fake-key", transport=transport)
    assert provider.is_configured() is True
    assert provider.name == "openai"

    finding = _dummy_finding()
    source = "import os\nos.system('ls ' + user_input)\n"
    fixes = provider.suggest_fix(source, finding)
    assert len(fixes) == 1
    fix = fixes[0]
    assert fix.kind == "llm"
    assert fix.title == "Use subprocess.run with argument array"
    assert "subprocess.run" in fix.edits[0].new_text


def test_anthropic_provider_with_mock_transport():
    """Verify AnthropicProvider parses response from mock transport."""

    def mock_handler(request: httpx.Request):
        assert request.url == "https://api.anthropic.com/v1/messages"
        assert request.headers.get("x-api-key") == "sk-ant-fake"
        payload = {
            "content": [
                {
                    "text": json.dumps(
                        {
                            "title": "Escape shell parameters",
                            "explanation": "Use shlex.quote to prevent command injection",
                            "replacement": "os.system(shlex.quote(user_input))",
                        }
                    )
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(mock_handler)
    provider = AnthropicProvider(api_key="sk-ant-fake", transport=transport)
    assert provider.is_configured() is True
    assert provider.name == "anthropic"

    finding = _dummy_finding()
    source = "import os\nos.system(user_input)\n"
    fixes = provider.suggest_fix(source, finding)
    assert len(fixes) == 1
    assert fixes[0].kind == "llm"
    assert "shlex.quote" in fixes[0].edits[0].new_text


def test_gemini_provider_with_mock_transport():
    """Verify GeminiProvider parses response from mock transport."""

    def mock_handler(request: httpx.Request):
        assert "generativelanguage.googleapis.com" in str(request.url)
        payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "title": "Use safe array execution",
                                        "explanation": "Prevents shell expansion",
                                        "replacement": "subprocess.run([cmd, arg])",
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(mock_handler)
    provider = GeminiProvider(api_key="fake-gemini-key", transport=transport)
    assert provider.is_configured() is True
    assert provider.name == "gemini"

    finding = _dummy_finding()
    source = "os.system(cmd)\n"
    fixes = provider.suggest_fix(source, finding)
    assert len(fixes) == 1
    assert fixes[0].kind == "llm"


def test_bad_llm_fix_is_downgraded_by_verifier():
    """Verify that an invalid LLM fix is rejected by verify_fix and downgraded to advice only."""
    # Source code with vulnerable os.system
    source = "import os\ncmd = input()\nos.system(cmd)\n"
    finding = _dummy_finding(line=3)

    # Provider generates a broken fix that introduces a syntax error
    def mock_handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "title": "Broken syntax attempt",
                                    "explanation": "This will fail syntax check",
                                    "replacement": "os.system(def invalid syntax",
                                }
                            )
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(mock_handler)
    provider = OpenAICompatProvider(api_key="sk-fake", transport=transport)
    fixes = provider.suggest_fix(source, finding)
    assert len(fixes) == 1
    bad_fix = fixes[0]

    # Run through the standard verifier (which automatically tests syntax & downgrades unverified fixes)
    verified_fix = verify_fix(source=source, fix=bad_fix, finding=finding, language="python")
    assert verified_fix.verification.verified is False
    assert verified_fix.confidence == "manual"
    assert len(verified_fix.edits) == 0
