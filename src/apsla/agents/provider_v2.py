"""Bounded, schema-checked model providers for the v2 agent boundary."""

from __future__ import annotations

import json
import os
import random
import re
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import httpx


def _load_env_file() -> None:
    """Best-effort loading of root .env configuration."""
    root_env = Path(__file__).resolve().parents[3] / ".env"
    if root_env.is_file():
        try:
            parsed: dict[str, str] = {}
            for raw_line in root_env.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k:
                    parsed[k] = v
            for k, v in parsed.items():
                os.environ[k] = v
        except Exception:
            pass


_load_env_file()

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
    raw_type = schema.get("type")
    typ = raw_type if isinstance(raw_type, str) else ""
    checks: dict[str, type[Any] | tuple[type[Any], ...]] = {
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
    text = re.sub(r"\bg[s]k_[A-Za-z0-9_-]+\b", "[REDACTED]", text)
    for key in ("GROQ_API_KEY",):
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
        self.last_tokens: int | None = None
        self.last_usage: dict[str, Any] = {}

    def _request(self, system: str, user: str, schema: dict[str, Any]) -> str:
        raise NotImplementedError

    def chat_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        if "required json schema" not in system.lower() and "schema" not in system.lower():
            system = f"{system}\nRequired JSON schema:\n{json.dumps(schema)}"
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
                clean_raw = raw.strip()
                if clean_raw.startswith("```"):
                    clean_raw = re.sub(r"^```(?:json)?\s*", "", clean_raw)
                    clean_raw = re.sub(r"\s*```$", "", clean_raw)
                parsed: Any = json.loads(clean_raw)
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


DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_FAST_MODEL = os.getenv("GROQ_MODEL_FAST", "openai/gpt-oss-20b")
DEFAULT_GROQ_CODE_MODEL = os.getenv("GROQ_MODEL_CODE", "openai/gpt-oss-120b")
_GROQ_MODELS_CACHE: dict[str, Any] = {"timestamp": 0.0, "models": []}
_GROQ_SEMAPHORE = threading.Semaphore(int(os.getenv("GROQ_MAX_CONCURRENCY", "2")))



class GroqProvider(HttpJsonProvider):
    name = "groq"
    processing_location = "remote"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        task: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        raw_key = api_key or os.getenv("GROQ_API_KEY")
        key = raw_key.strip().strip("'\"") if raw_key else ""
        if not key:
            raise ProviderFailure(
                "unavailable",
                "Add GROQ_API_KEY to your .env file and restart",
                "Add GROQ_API_KEY to your .env file and restart",
            )
        url = (base_url or os.getenv("GROQ_BASE_URL") or DEFAULT_GROQ_BASE_URL).rstrip("/")
        if model:
            chosen_model = model
        elif task in {"fast", "explain"}:
            chosen_model = os.getenv("GROQ_MODEL_FAST") or DEFAULT_GROQ_FAST_MODEL
        else:
            chosen_model = (
                os.getenv("GROQ_MODEL_CODE")
                or os.getenv("GROQ_MODEL")
                or DEFAULT_GROQ_CODE_MODEL
            )

        if kwargs.get("transport") is None:
            try:
                available = self.list_models(api_key=key, base_url=url)
                if available and chosen_model not in available:
                    chosen_model = available[0]
            except Exception:
                pass

        timeout_val = timeout
        if timeout_val is None:
            timeout_val = float(
                os.getenv(
                    "GROQ_TIMEOUT_SECONDS",
                    os.getenv("SECURELEX_AI_TIMEOUT_SECONDS", "30.0"),
                )
            )

        super().__init__(
            url,
            chosen_model,
            timeout=timeout_val,
            api_key=key,
            **kwargs,
        )

    def _request(self, system: str, user: str, schema: dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        max_tokens = min(int(os.getenv("GROQ_MAX_TOKENS", "4096")), 8192)
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        if not any("json" in m["content"].lower() for m in messages):
            messages[0]["content"] += "\nReturn output in valid JSON format."
        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        acquired = _GROQ_SEMAPHORE.acquire(timeout=self.timeout)
        if not acquired:
            raise ProviderFailure(
                "concurrency_limit",
                "Groq provider concurrency limit reached.",
                "Wait for ongoing requests to finish, then retry.",
            )
        try:
            max_retries = 4
            last_error: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    with httpx.Client(
                        transport=self.transport, timeout=self.timeout, headers=headers
                    ) as client:
                        response = client.post(
                            f"{self.base_url}/chat/completions",
                            json=payload,
                        )
                        if response.status_code == 400:
                            resp_body: dict[str, Any] = {}
                            try:
                                resp_body = response.json()
                            except Exception:
                                pass
                            err_data: dict[str, Any] = resp_body.get("error", {}) if isinstance(resp_body.get("error"), dict) else {}
                            err_msg = str(err_data.get("message", resp_body.get("message", "")))
                            err_code = str(err_data.get("code", resp_body.get("code", "")))
                            fg = resp_body.get("failed_generation") or err_data.get("failed_generation")
                            is_json_err = (
                                err_code == "json_validate_failed"
                                or "failed to validate json" in err_msg.lower()
                                or "json" in err_msg.lower()
                                or bool(fg)
                            )
                            if is_json_err:
                                # Fallback: retry without strict response_format so model output is returned
                                fallback_payload = dict(payload)
                                fallback_payload.pop("response_format", None)
                                try:
                                    fb_resp = client.post(
                                        f"{self.base_url}/chat/completions",
                                        json=fallback_payload,
                                    )
                                    if fb_resp.status_code == 200:
                                        fb_data = fb_resp.json()
                                        fb_choices = fb_data.get("choices", [])
                                        if fb_choices:
                                            raw_content = str(fb_choices[0].get("message", {}).get("content", ""))
                                            # If raw_content is valid JSON, return it
                                            try:
                                                json.loads(raw_content)
                                                return raw_content
                                            except Exception:
                                                # Check if JSON is inside a code block ```json ... ```
                                                json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_content)
                                                if json_match:
                                                    try:
                                                        json.loads(json_match.group(1))
                                                        return json_match.group(1)
                                                    except Exception:
                                                        pass
                                                # Adapt into expected schema if reply field is requested
                                                props = schema.get("properties", {})
                                                if "reply" in props:
                                                    return json.dumps({"reply": raw_content, "code_snippets": []})
                                                elif "explanation" in props:
                                                    return json.dumps({"explanation": raw_content})
                                                return raw_content
                                except Exception:
                                    pass
                                if fg:
                                    clean_fg = str(fg).strip()
                                    json_match = re.search(r"(\{[\s\S]*\})", clean_fg)
                                    if json_match:
                                        try:
                                            json.loads(json_match.group(1))
                                            return json_match.group(1)
                                        except Exception:
                                            pass
                                    props = schema.get("properties", {})
                                    if "reply" in props:
                                        return json.dumps({"reply": clean_fg, "code_snippets": []})
                                    elif "explanation" in props:
                                        return json.dumps({"explanation": clean_fg})
                                detail = fg or err_msg or ""
                                raise ProviderFailure(
                                    "bad_output",
                                    f"Provider JSON generation failed ({detail}).",
                                    "Increase GROQ_MAX_TOKENS or simplify the request prompt.",
                                )
                        if response.status_code == 401:
                            raise ProviderFailure(
                                "invalid_key",
                                "Groq API key is invalid or unauthorized.",
                                "Verify GROQ_API_KEY in .env.",
                            )
                        if response.status_code == 404:
                            raise ProviderFailure(
                                "model_unavailable",
                                f"Groq model '{self.model}' is not available.",
                                "Select a supported Groq model.",
                            )
                        if response.status_code == 429:
                            if attempt < max_retries:
                                retry_after = response.headers.get("Retry-After")
                                delay = 1.0 * (1.5**attempt) + random.uniform(0.1, 0.4)
                                if retry_after:
                                    try:
                                        delay = max(float(retry_after), 1.0)
                                    except ValueError:
                                        pass
                                time.sleep(delay)
                                continue
                            raise ProviderFailure(
                                "rate_limited",
                                "Groq rate limit reached.",
                                "Please wait a moment before trying again.",
                            )
                        if response.status_code >= 500:
                            if attempt < max_retries:
                                time.sleep(0.5 * (2**attempt))
                                continue
                            raise ProviderFailure(
                                "provider_error",
                                f"Groq service error (HTTP {response.status_code}).",
                                "Check Groq service status, then retry.",
                            )
                        response.raise_for_status()
                        data = response.json()
                        self.last_usage = data.get("usage", {})
                        self.last_tokens = self.last_usage.get("total_tokens")
                        choices = data.get("choices", [])
                        if not choices:
                            raise ProviderFailure(
                                "bad_output",
                                "Groq returned an empty choice set.",
                                "Retry the request.",
                            )
                        return str(choices[0].get("message", {}).get("content", ""))
                except (httpx.TransportError, httpx.NetworkError) as net_err:
                    last_error = net_err
                    if attempt < max_retries:
                        time.sleep(0.5 * (2**attempt))
                        continue
                    raise ProviderFailure(
                        "network_error",
                        "Network error connecting to Groq API.",
                        "Check your internet connection and proxy settings.",
                    ) from net_err
                except httpx.TimeoutException as timeout_err:
                    raise ProviderFailure(
                        "timeout",
                        f"Groq request timed out after {self.timeout}s.",
                        "Increase GROQ_TIMEOUT_SECONDS in .env or try a faster model.",
                    ) from timeout_err
            if last_error:
                raise last_error
            raise ProviderFailure("provider_error", "Groq request failed after retries.")
        finally:
            _GROQ_SEMAPHORE.release()

    @classmethod
    def list_models(
        cls,
        base_url: str | None = None,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> list[str]:
        now = time.time()
        if _GROQ_MODELS_CACHE["models"] and (now - _GROQ_MODELS_CACHE["timestamp"]) < 300:
            return list(_GROQ_MODELS_CACHE["models"])

        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            return [DEFAULT_GROQ_CODE_MODEL, DEFAULT_GROQ_FAST_MODEL]
        url = (base_url or os.getenv("GROQ_BASE_URL") or DEFAULT_GROQ_BASE_URL).rstrip("/")
        headers = {"Authorization": f"Bearer {key}"}
        try:
            with httpx.Client(transport=transport, timeout=timeout, headers=headers) as client:
                res = client.get(f"{url}/models")
                if res.status_code == 200:
                    data = res.json()
                    models = [
                        item["id"]
                        for item in data.get("data", [])
                        if isinstance(item, dict) and "id" in item
                    ]
                    chat_models = [
                        m
                        for m in models
                        if not any(
                            x in m.lower()
                            for x in ["whisper", "guard", "embed", "tts", "distil-whisper"]
                        )
                    ]
                    priority = [
                        DEFAULT_GROQ_CODE_MODEL,
                        DEFAULT_GROQ_FAST_MODEL,
                        "openai/gpt-oss-120b",
                        "openai/gpt-oss-20b",
                        "llama-3.3-70b-versatile",
                        "llama-3.1-8b-instant",
                    ]
                    sorted_models = [m for m in priority if m in chat_models] + [
                        m for m in chat_models if m not in priority
                    ]
                    final_models = sorted_models or models
                    _GROQ_MODELS_CACHE["timestamp"] = now
                    _GROQ_MODELS_CACHE["models"] = final_models
                    return list(final_models)
        except Exception:
            pass
        return [DEFAULT_GROQ_CODE_MODEL, DEFAULT_GROQ_FAST_MODEL]

    @classmethod
    def test_connection(
        cls,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        raw_key = api_key or os.getenv("GROQ_API_KEY")
        key = raw_key.strip().strip("'\"") if raw_key else ""
        if not key:
            return {
                "ok": False,
                "provider": "groq",
                "latency_ms": 0.0,
                "model": None,
                "available_models": [],
                "error": "Add GROQ_API_KEY to your .env file and restart",
            }
        url = (base_url or os.getenv("GROQ_BASE_URL") or DEFAULT_GROQ_BASE_URL).rstrip("/")
        headers = {"Authorization": f"Bearer {key}"}
        t0 = time.perf_counter()
        try:
            with httpx.Client(transport=transport, timeout=timeout, headers=headers) as client:
                res = client.get(f"{url}/models")
                latency = round((time.perf_counter() - t0) * 1000, 2)
                if res.status_code == 401:
                    return {
                        "ok": False,
                        "provider": "groq",
                        "latency_ms": latency,
                        "model": None,
                        "available_models": [],
                        "error": "Invalid Groq API key (401 Unauthorized)",
                    }
                if res.status_code != 200:
                    return {
                        "ok": False,
                        "provider": "groq",
                        "latency_ms": latency,
                        "model": None,
                        "available_models": [],
                        "error": f"Groq returned HTTP status {res.status_code}",
                    }
                data = res.json()
                models = [
                    item["id"]
                    for item in data.get("data", [])
                    if isinstance(item, dict) and "id" in item
                ]
                chat_models = [
                    m
                    for m in models
                    if not any(
                        x in m.lower()
                        for x in [
                            "whisper",
                            "guard",
                            "embed",
                            "tts",
                            "distil-whisper",
                        ]
                    )
                ]
                priority = [
                    DEFAULT_GROQ_CODE_MODEL,
                    DEFAULT_GROQ_FAST_MODEL,
                    "llama-3.1-70b-versatile",
                    "llama3-70b-8192",
                    "llama3-8b-8192",
                ]
                sorted_models = [m for m in priority if m in chat_models] + [
                    m for m in chat_models if m not in priority
                ]
                final_models = sorted_models or models
                chosen = model or (final_models[0] if final_models else DEFAULT_GROQ_CODE_MODEL)
                return {
                    "ok": True,
                    "provider": "groq",
                    "latency_ms": latency,
                    "model": chosen,
                    "available_models": final_models,
                    "error": None,
                }
        except httpx.TimeoutException:
            return {
                "ok": False,
                "provider": "groq",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                "model": None,
                "available_models": [],
                "error": f"Connection timed out after {timeout}s",
            }
        except Exception as exc:
            err_msg = redact_prompt(str(exc))
            return {
                "ok": False,
                "provider": "groq",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                "model": None,
                "available_models": [],
                "error": f"Connection failed: {err_msg}",
            }


def provider_from_environment(task: str | None = None) -> ModelProvider:
    if os.getenv("SECURELEX_ENV") == "test" and os.getenv("SECURELEX_AI_PROVIDER") == "fake":
        return FakeProvider()
    choice = os.getenv("SECURELEX_AI_PROVIDER", "groq").strip().lower()
    if choice != "groq":
        raise ProviderFailure(
            "invalid_provider",
            f"Unsupported AI provider '{choice}'. Only 'groq' is supported.",
            "Set SECURELEX_AI_PROVIDER=groq in .env.",
        )
    return GroqProvider(task=task)



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
    subject_type: str | None = None
    subject_id: str | None = None
    provider: str | None = None
    model: str | None = None
    tokens: int | None = None


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
        subject_type: str | None = None,
        subject_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        tokens: int | None = None,
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
            subject_type,
            subject_id,
            provider,
            model,
            tokens,
        )
        self._events.append(event)
        return event

    def query(self, operation_id: str | None = None) -> list[AgentEvent]:
        return [
            event
            for event in self._events
            if operation_id is None or event.operation_id == operation_id
        ]

    def remove(self, operation_ids: set[str]) -> None:
        self._events = deque(
            (event for event in self._events if event.operation_id not in operation_ids),
            maxlen=self._events.maxlen,
        )


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
