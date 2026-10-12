"""Bounded, schema-checked model providers for the v2 agent boundary."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

MAX_PROMPT_BYTES = 512 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
MAX_OUTPUT_TOKENS = 2048
REMOTE_CONSENT_REQUIRED = "Remote processing requires explicit consent for this session."


class ProviderFailure(RuntimeError):
    """Typed provider failure safe to return to an API client."""

    def __init__(self, kind: str, message: str, retry_guidance: str = "") -> None:
        super().__init__(message)
        self.kind, self.retry_guidance = kind, retry_guidance


class ModelProvider(Protocol):
    name: str
    processing_location: str
    model: str

    def chat_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]: ...


def validate_json_schema(value: Any, schema: dict[str, Any]) -> bool:
    """Validate the JSON Schema subset used by our structured agent outputs."""
    if not isinstance(schema, dict):
        return False
    typ = schema.get("type")
    checks = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
    }
    expected = checks.get(typ)
    if expected is not None and (
        not isinstance(value, expected)
        or (typ in {"integer", "number"} and isinstance(value, bool))
    ):
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if typ == "object":
        if any(key not in value for key in schema.get("required", [])):
            return False
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and any(key not in props for key in value):
            return False
        if any(
            key in props and not validate_json_schema(item, props[key])
            for key, item in value.items()
        ):
            return False
    if typ == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 10000):
            return False
        if "items" in schema and any(
            not validate_json_schema(item, schema["items"]) for item in value
        ):
            return False
    return not (
        typ == "string"
        and (
            len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 1000000)
        )
    )


def redact_prompt(text: str) -> str:
    text = re.sub(
        r"(?i)(api[_-]?key|token|password|secret)(\s*[:=]\s*)([^\s,;]+)", r"\1\2[REDACTED]", text
    )
    for key in ("OPENAI_COMPAT_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        secret = os.environ.get(key)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


def frame_untrusted(label: str, content: str) -> str:
    escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<UNTRUSTED_{label}>\n{escaped}\n</UNTRUSTED_{label}>"


class HttpJsonProvider:
    processing_location = "local"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 15.0,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url, self.model, self.timeout, self.api_key, self.transport = (
            base_url.rstrip("/"),
            model,
            timeout,
            api_key,
            transport,
        )
        self.call_count = 0

    def _request(self, system: str, user: str, schema: dict[str, Any]) -> str:
        raise NotImplementedError

    def chat_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        system, user = redact_prompt(system), redact_prompt(user)
        if len((system + user).encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ProviderFailure(
                "request_limit",
                "Model request exceeds the configured size limit.",
                "Reduce the source or request size and retry.",
            )
        last = "Provider did not return valid structured output."
        for attempt in range(2):
            self.call_count += 1
            try:
                request_system = system
                if attempt:
                    request_system += (
                        "\nRepair attempt: the previous output failed structured-output validation. "
                        f"Failure: {last} Return only a corrected JSON object matching the schema."
                    )
                raw = self._request(request_system, user, schema)
                if len(raw.encode("utf-8")) > MAX_RESPONSE_BYTES:
                    raise ProviderFailure(
                        "response_limit",
                        "Provider output exceeds the configured response-size limit.",
                        "Reduce output length and retry.",
                    )
                parsed = json.loads(raw)
                if validate_json_schema(parsed, schema):
                    return parsed
                last = "Provider output did not match the required JSON schema."
            except httpx.TimeoutException as exc:
                last = f"Provider request timed out ({type(exc).__name__})."
            except httpx.HTTPStatusError as exc:
                last = f"Provider returned HTTP status {exc.response.status_code}."
            except (httpx.RequestError, ValueError, json.JSONDecodeError) as exc:
                last = f"Provider request failed: {type(exc).__name__}."
            if attempt == 0:
                time.sleep(0.1)
        raise ProviderFailure(
            "provider_error", last, "Check provider status/model setup, then retry."
        )


class OllamaProvider(HttpJsonProvider):
    name = "ollama"

    def __init__(
        self, base_url: str | None = None, model: str | None = None, **kwargs: Any
    ) -> None:
        url = base_url or os.getenv(
            "OLLAMA_BASE_URL", os.getenv("APSLA_LOCAL_URL", "http://127.0.0.1:11434")
        )
        host = (urlparse(url).hostname or "").lower().strip("[]")
        if host not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Ollama provider must use a loopback address.")
        super().__init__(
            url,
            model or os.getenv("OLLAMA_MODEL", os.getenv("APSLA_LOCAL_MODEL", "qwen2.5-coder:3b")),
            **kwargs,
        )

    def _request(self, system: str, user: str, schema: dict[str, Any]) -> str:
        with httpx.Client(transport=self.transport, timeout=self.timeout) as client:
            response = client.post(
                self.base_url + "/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "format": schema,
                    "stream": False,
                    "options": {"num_predict": MAX_OUTPUT_TOKENS},
                },
            )
            response.raise_for_status()
            return str(response.json().get("message", {}).get("content", ""))


class OpenAICompatibleProvider(HttpJsonProvider):
    name = "openai-compatible"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            base_url or os.getenv("OPENAI_COMPAT_BASE_URL", ""),
            model or os.getenv("OPENAI_COMPAT_MODEL", ""),
            api_key=api_key if api_key is not None else os.getenv("OPENAI_COMPAT_API_KEY"),
            **kwargs,
        )
        if not self.base_url or not self.model:
            raise ProviderFailure(
                "unavailable",
                "OpenAI-compatible provider is not configured.",
                "Set OPENAI_COMPAT_BASE_URL, OPENAI_COMPAT_MODEL and OPENAI_COMPAT_API_KEY.",
            )
        host = (urlparse(self.base_url).hostname or "").lower()
        try:
            loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = host == "localhost"
        self.processing_location = "local" if loopback else "remote"
        if self.processing_location == "remote" and not self.api_key:
            raise ProviderFailure(
                "unavailable",
                "Remote OpenAI-compatible provider has no API key configured.",
                "Set OPENAI_COMPAT_API_KEY in the server environment.",
            )

    def _request(self, system: str, user: str, schema: dict[str, Any]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        with httpx.Client(
            transport=self.transport, timeout=self.timeout, headers=headers
        ) as client:
            response = client.post(
                self.base_url + "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": MAX_OUTPUT_TOKENS,
                },
                headers=headers,
            )
            response.raise_for_status()
            return str(response.json()["choices"][0]["message"]["content"])


def provider_from_environment() -> ModelProvider:
    choice = os.getenv("SECURELEX_AI_PROVIDER", "ollama").strip().lower()
    if choice in {"openai", "openai-compatible"}:
        return OpenAICompatibleProvider()
    return OllamaProvider()


class FakeProvider:
    """Deterministic provider test double; no network access."""

    name, processing_location, model = "fake", "local", "fake-test-provider"

    def __init__(self, responses: list[Any] | None = None, delay: float = 0) -> None:
        self.responses, self.delay, self.call_count = deque(responses or []), delay, 0

    def chat_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        import time as _time

        self.call_count += 1
        if self.delay:
            _time.sleep(self.delay)
        if not self.responses:
            raise ProviderFailure("unavailable", "Fake provider has no canned response.")
        result = self.responses.popleft()
        if isinstance(result, Exception):
            raise result
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError as exc:
                raise ProviderFailure("invalid_json", "Provider returned invalid JSON.") from exc
        if not validate_json_schema(result, schema):
            raise ProviderFailure(
                "schema_invalid", "Provider output did not match the required JSON schema."
            )
        return result


@dataclass
class AgentEvent:
    id: str
    timestamp: str
    operation_id: str
    agent: str
    action: str
    tool: str | None
    argument_summary: str
    decision_source: str
    outcome: str
    duration: float
    error: str | None = None


class AgentEventLog:
    def __init__(self, capacity: int = 1000) -> None:
        self._events: deque[AgentEvent] = deque(maxlen=capacity)

    def add(
        self,
        operation_id: str,
        agent: str,
        action: str,
        tool: str | None,
        argument_summary: str,
        decision_source: str,
        outcome: str,
        duration: float,
        error: str | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            str(uuid.uuid4()),
            datetime.now(UTC).isoformat(),
            operation_id,
            agent,
            action,
            tool,
            argument_summary[:160],
            decision_source,
            outcome,
            round(duration, 3),
            (error or "")[:240] or None,
        )
        self._events.append(event)
        return event

    def query(self, operation_id: str | None = None) -> list[AgentEvent]:
        return [
            event
            for event in self._events
            if operation_id is None or event.operation_id == operation_id
        ]


class ToolGateway:
    """Explicit permission boundary over in-memory analysis and patch validation."""

    ALLOWLIST = {
        "unicode_scan",
        "relex_with_recovery",
        "lex_stats",
        "detect_language_candidates",
        "parse_structure",
        "run_rules",
        "run_taint",
        "ml_score",
        "build_explanation",
        "finish",
        "list_fix_candidates",
        "apply_fix_to_copy",
        "verify_fix",
        "rescan_copy",
        "validate_patch",
    }
    SCHEMAS: dict[str, dict[str, Any]] = {
        name: {"type": "object", "properties": {}, "additionalProperties": False}
        for name in ALLOWLIST
    }
    SCHEMAS["relex_with_recovery"] = {
        "type": "object",
        "properties": {"language": {"type": "string"}},
        "additionalProperties": False,
    }
    SCHEMAS["detect_language_candidates"] = {
        "type": "object",
        "properties": {"filename": {"type": "string"}},
        "additionalProperties": False,
    }
    SCHEMAS["parse_structure"] = {
        "type": "object",
        "properties": {"language": {"type": "string"}},
        "additionalProperties": False,
    }
    SCHEMAS["run_rules"] = {
        "type": "object",
        "properties": {"language": {"type": "string"}},
        "additionalProperties": False,
    }
    SCHEMAS["run_taint"] = {
        "type": "object",
        "properties": {"mode": {"type": "string", "enum": ["shallow", "deep"]}},
        "additionalProperties": False,
    }
    SCHEMAS["build_explanation"] = {
        "type": "object",
        "properties": {"finding_id": {"type": "string"}},
        "required": ["finding_id"],
        "additionalProperties": False,
    }
    SCHEMAS["validate_patch"] = {
        "type": "object",
        "properties": {
            "finding_id": {"type": "string"},
            "patch": {"type": "string", "maxLength": 131072},
        },
        "required": ["finding_id", "patch"],
        "additionalProperties": False,
    }
    for _name in ("list_fix_candidates", "apply_fix_to_copy", "verify_fix"):
        SCHEMAS[_name] = {
            "type": "object",
            "properties": {"finding_id": {"type": "string"}, "fix_id": {"type": "string"}},
            "additionalProperties": False,
        }
    SCHEMAS["run_taint"] = {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["normal", "deep"]},
            "focus_sinks": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["mode"],
        "additionalProperties": False,
    }
    PERMISSIONS = {name: {"read"} for name in ALLOWLIST}
    PERMISSIONS["validate_patch"] = {"validate"}
    PERMISSIONS["apply_fix_to_copy"] = {"validate"}
    PERMISSIONS["verify_fix"] = {"validate"}

    def __init__(self, budget: int = 12, timeout_seconds: float = 2.0) -> None:
        self.budget, self.calls, self.timeout_seconds = budget, 0, timeout_seconds

    def call(self, tool: str, operation: str, parameters: dict[str, Any], executor: Any) -> Any:
        if tool not in self.ALLOWLIST or operation not in self.PERMISSIONS.get(tool, set()):
            raise PermissionError("Tool operation is not allowed by the analysis gateway.")
        if self.calls >= self.budget:
            raise PermissionError("Tool call budget exhausted.")
        if (
            not isinstance(parameters, dict)
            or len(json.dumps(parameters, ensure_ascii=False).encode("utf-8")) > 8192
        ):
            raise ValueError("Tool parameters exceed the gateway schema limit.")
        if not validate_json_schema(parameters, self.SCHEMAS[tool]):
            raise ValueError("Tool parameters do not match the registered JSON schema.")
        self.calls += 1
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(executor)
        try:
            result = future.result(timeout=self.timeout_seconds)
            if (
                len(json.dumps(result, ensure_ascii=False, default=str).encode("utf-8"))
                > MAX_RESPONSE_BYTES
            ):
                raise ValueError("Tool output exceeds the gateway response-size limit.")
            return result
        except FutureTimeout as exc:
            future.cancel()
            raise TimeoutError(f"Tool '{tool}' exceeded its time budget.") from exc
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
