"""Explicitly gated deterministic provider used only by endpoint integration tests."""

from __future__ import annotations

from apsla.server.app import _provider_for_session


def test_fake_ai_provider_requires_test_environment_and_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("SECURELEX_ENV", "test")
    monkeypatch.setenv("SECURELEX_TEST_AI_PROVIDER", "1")
    provider = _provider_for_session("test-session-123456", False)
    assert provider.name == "test-only-fake"
    assert provider.processing_location == "local"
    explain = provider.chat_json("", "", {"type": "object", "properties": {"explanation": {"type": "string"}}})
    assert explain["explanation"].startswith("Deterministic test explanation")
    generated = provider.chat_json("", '<UNTRUSTED_REQUIREMENTS> ["test requirement"] </UNTRUSTED_REQUIREMENTS>', {
        "type": "object", "properties": {
            "language": {"type": "string"}, "code": {"type": "string"},
            "explanation": {"type": "string"}, "assumptions": {"type": "array"},
            "requirements_checklist": {"type": "array"},
        },
    })
    assert generated["language"] == "cpp"
    assert generated["code"] == "int main() { return 0; }\n"
    assert generated["requirements_checklist"][0]["status"] == "unverified"


def test_fake_ai_provider_is_not_enabled_in_production(monkeypatch):
    monkeypatch.setenv("SECURELEX_ENV", "production")
    monkeypatch.setenv("SECURELEX_TEST_AI_PROVIDER", "1")
    try:
        provider = _provider_for_session("test-session-123456", False)
    except Exception as error:
        assert getattr(error, "detail", "") != "test-only-fake"
    else:
        assert provider.name != "test-only-fake", "Production configuration must not select the test provider"
