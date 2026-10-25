"""Unit tests for LocalLLM and local Ollama client (Phase 15)."""

import importlib
import json

import httpx
import pytest

from apsla.llm.local_ollama import (
    LocalLLM,
    get_agent_status,
    validate_loopback_url,
    validate_schema,
)


def test_loopback_url_security_validation():
    # Valid loopback hosts
    assert validate_loopback_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"
    assert validate_loopback_url("http://localhost:11434") == "http://localhost:11434"
    assert validate_loopback_url("http://[::1]:11434") == "http://[::1]:11434"

    # External hosts must be strictly rejected
    with pytest.raises(ValueError, match="Security violation"):
        validate_loopback_url("http://api.openai.com/v1")

    with pytest.raises(ValueError, match="Security violation"):
        validate_loopback_url("http://192.168.1.5:11434")

    with pytest.raises(ValueError, match="Security violation"):
        validate_loopback_url("http://evil-server.org")


def test_schema_validator():
    schema = {
        "type": "object",
        "required": ["action", "args"],
        "properties": {
            "action": {"type": "string", "enum": ["run_rules", "finish"]},
            "args": {"type": "object"},
        },
    }

    assert validate_schema({"action": "run_rules", "args": {}}, schema) is True
    # Missing required
    assert validate_schema({"action": "run_rules"}, schema) is False
    # Bad enum
    assert validate_schema({"action": "unknown", "args": {}}, schema) is False
    # Bad type
    assert validate_schema(["not an object"], schema) is False


def test_local_llm_chat_json_success():
    expected_response = {
        "message": {"content": json.dumps({"reason": "All done", "action": "finish", "args": {}})}
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json=expected_response)

    transport = httpx.MockTransport(handler)
    client = LocalLLM(transport=transport)

    schema = {
        "type": "object",
        "required": ["reason", "action", "args"],
        "properties": {
            "action": {"type": "string"},
            "args": {"type": "object"},
        },
    }
    result = client.chat_json("system prompt", "user prompt", schema=schema)
    assert result == {"reason": "All done", "action": "finish", "args": {}}
    assert client.call_count == 1


def test_local_llm_retry_on_bad_json():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            # First attempt: garbage JSON
            return httpx.Response(200, json={"message": {"content": "not json at all"}})
        # Second attempt: valid JSON
        return httpx.Response(
            200,
            json={"message": {"content": json.dumps({"action": "finish", "args": {}})}},
        )

    transport = httpx.MockTransport(handler)
    client = LocalLLM(transport=transport)
    result = client.chat_json("sys", "user")
    assert result == {"action": "finish", "args": {}}
    assert attempts == 2
    assert client.call_count == 2


def test_get_agent_status_mocked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"models": [{"name": "qwen2.5-coder:3b:latest"}]},
        )

    transport = httpx.MockTransport(handler)
    status = get_agent_status(transport=transport, override_mode="local")
    assert status["ollama_reachable"] is True
    assert status["model_present"] is True
    assert status["fallback_active"] is False
    assert status["mode"] == "local"


def test_get_agent_status_selects_installed_model_from_configured_family(monkeypatch):
    module = importlib.import_module("apsla.llm.local_ollama")
    monkeypatch.setattr(module, "_load_env_file", lambda: None)
    monkeypatch.setenv("APSLA_LOCAL_MODEL", "qwen2.5-coder:3b")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"models": [{"name": "qwen2.5-coder:1.5b"}, {"name": "llama3:8b"}]},
        )

    status = get_agent_status(transport=httpx.MockTransport(handler), override_mode="local")
    assert status["model_present"] is True
    assert status["model"] == "qwen2.5-coder:1.5b"
    assert status["models"] == ["qwen2.5-coder:1.5b", "llama3:8b"]


def test_get_agent_status_reports_exact_pull_command_when_model_family_missing(monkeypatch):
    module = importlib.import_module("apsla.llm.local_ollama")
    monkeypatch.setattr(module, "_load_env_file", lambda: None)
    monkeypatch.setenv("APSLA_LOCAL_MODEL", "qwen2.5-coder:3b")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "llama3:8b"}]})

    status = get_agent_status(transport=httpx.MockTransport(handler), override_mode="local")
    assert status["model_present"] is False
    assert status["message"] == "Model unavailable. Run: ollama pull qwen2.5-coder:3b"
