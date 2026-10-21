"""Unit tests for the Groq hybrid AI provider and capability routing (G1)."""

from __future__ import annotations

import json

import httpx
import pytest
from fastapi import HTTPException

from apsla.agents.provider_v2 import (
    DEFAULT_GROQ_CODE_MODEL,
    DEFAULT_GROQ_FAST_MODEL,
    GroqProvider,
    ProviderFailure,
    provider_from_environment,
    redact_prompt,
)
from apsla.server.app import (
    REMOTE_CONSENTS,
    _provider_for_session,
    build_capabilities,
)

SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {"type": "string", "minLength": 1},
        "score": {"type": "integer"},
    },
    "required": ["analysis", "score"],
    "additionalProperties": False,
}


def test_groq_provider_missing_key_raises_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderFailure) as exc_info:
        GroqProvider(api_key=None)
    assert exc_info.value.kind == "unavailable"
    assert "not configured" in str(exc_info.value)


def test_groq_provider_success_structured_output() -> None:
    expected_data = {"analysis": "No security defects detected.", "score": 100}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/openai/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer mock-test-key"
        body = json.loads(request.content)
        assert body["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(expected_data),
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    provider = GroqProvider(api_key="mock-test-key", transport=transport)
    result = provider.chat_json("Analyze security.", "def test(): pass", SCHEMA)
    assert result == expected_data
    assert provider.call_count == 1


def test_groq_provider_schema_repair_attempt() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            # First attempt returns invalid JSON schema
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps({"wrong_field": 123}),
                            }
                        }
                    ]
                },
            )
        # Second attempt returns repaired, valid schema
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps({"analysis": "Repaired valid output", "score": 90}),
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    provider = GroqProvider(api_key="mock-test-key", transport=transport)
    result = provider.chat_json("Analyze code.", "code snippet", SCHEMA)
    assert result == {"analysis": "Repaired valid output", "score": 90}
    assert provider.call_count == 2
    assert calls == 2


def test_groq_provider_401_invalid_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "Invalid API Key"}})

    transport = httpx.MockTransport(handler)
    provider = GroqProvider(api_key="mock-bad-key", transport=transport)
    with pytest.raises(ProviderFailure) as exc_info:
        provider.chat_json("System", "User", SCHEMA)
    assert exc_info.value.kind == "invalid_key"


def test_groq_provider_429_rate_limit_retry_and_fail() -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(429, headers={"Retry-After": "0.01"}, json={"error": {"message": "Rate limit"}})

    transport = httpx.MockTransport(handler)
    provider = GroqProvider(api_key="mock-test-key", transport=transport)
    with pytest.raises(ProviderFailure):
        provider.chat_json("System", "User", SCHEMA)
    # Retries occurred
    assert call_count >= 2


def test_groq_provider_timeout_handling() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout waiting for Groq")

    transport = httpx.MockTransport(handler)
    provider = GroqProvider(api_key="mock-test-key", transport=transport, timeout=1.0)
    with pytest.raises(ProviderFailure):
        provider.chat_json("System", "User", SCHEMA)


def test_groq_provider_redacts_api_key_and_gsk() -> None:
    fake_secret = "gsk_1234567890abcdef1234567890abcdef"
    text = f"Bearer {fake_secret} and api_key: {fake_secret}"
    redacted = redact_prompt(text)
    assert fake_secret not in redacted
    assert "[REDACTED]" in redacted


def test_groq_provider_task_model_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "mock-test-key")
    fast_provider = GroqProvider(task="explain")
    assert fast_provider.model == DEFAULT_GROQ_FAST_MODEL

    code_provider = GroqProvider(task="code")
    assert code_provider.model == DEFAULT_GROQ_CODE_MODEL


def test_provider_from_environment_auto_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECURELEX_AI_PROVIDER", "auto")
    monkeypatch.setenv("GROQ_API_KEY", "mock-key-present")
    prov = provider_from_environment()
    assert isinstance(prov, GroqProvider)
    assert prov.name == "groq"
    assert prov.processing_location == "remote"

    # When key is removed, falls back to Ollama
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    prov_fallback = provider_from_environment()
    assert prov_fallback.name == "ollama"
    assert prov_fallback.processing_location == "local"


def test_groq_list_models_mock() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "whisper-large-v3"},
                    {"id": "llama-3.1-8b-instant"},
                    {"id": "llama-3.3-70b-versatile"},
                    {"id": "qwen-2.5-coder-32b"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    models = GroqProvider.list_models(api_key="mock-key", transport=transport)
    assert "llama-3.3-70b-versatile" in models
    assert "llama-3.1-8b-instant" in models
    # Audio whisper models filtered out
    assert "whisper-large-v3" not in models


def test_groq_test_connection_mock() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "llama-3.3-70b-versatile"},
                    {"id": "llama-3.1-8b-instant"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    result = GroqProvider.test_connection(api_key="mock-key", transport=transport)
    assert result["ok"] is True
    assert result["provider"] == "groq"
    assert result["latency_ms"] >= 0
    assert "llama-3.3-70b-versatile" in result["available_models"]


def test_capabilities_groq_remote_does_not_require_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECURELEX_ENV", raising=False)
    monkeypatch.setenv("SECURELEX_AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "mock-groq-key")

    import apsla.llm.local_ollama as ollama_mod

    # Simulate Ollama completely offline
    monkeypatch.setattr(
        ollama_mod,
        "get_agent_status",
        lambda: {"ollama_reachable": False, "model_present": False, "model": "none", "models": []},
    )

    caps = build_capabilities(session_id="test-session-groq-1234")
    assert caps.ai["provider"] == "groq"
    assert caps.ai["processing_location"] == "remote"
    assert caps.ai["consent_required"] is True
    assert caps.ai["configured"] is True

    # Before remote consent, build_with_ai is False
    assert caps.features["build_with_ai"] is False

    # After remote consent is granted, build_with_ai and fix_with_ai become True WITHOUT Ollama
    REMOTE_CONSENTS.add("test-session-groq-1234")
    try:
        caps_consented = build_capabilities(session_id="test-session-groq-1234")
        assert caps_consented.ai["remote_consented"] is True
        assert caps_consented.features["build_with_ai"] is True
        assert caps_consented.features["fix_with_ai"] is True
    finally:
        REMOTE_CONSENTS.discard("test-session-groq-1234")


def test_provider_for_session_enforces_consent_for_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECURELEX_ENV", raising=False)
    monkeypatch.setenv("SECURELEX_AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "mock-groq-key")

    test_session = "unconsented-session-uuid-1234"
    REMOTE_CONSENTS.discard(test_session)

    # Calling without consent raises 403
    with pytest.raises(HTTPException) as exc_info:
        _provider_for_session(test_session, remote_consent=False)
    assert exc_info.value.status_code == 403
    assert "Remote processing requires explicit consent" in exc_info.value.detail

    # Calling with consent succeeds
    REMOTE_CONSENTS.add(test_session)
    try:
        provider = _provider_for_session(test_session, remote_consent=True)
        assert provider.name == "groq"
        assert provider.processing_location == "remote"
    finally:
        REMOTE_CONSENTS.discard(test_session)
