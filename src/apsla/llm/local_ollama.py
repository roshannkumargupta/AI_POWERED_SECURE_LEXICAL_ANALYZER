"""Local Ollama client for local-only LLM-assisted analysis (Phase 15).

STRICT SECURITY CONSTRAINTS:
- Host MUST be strictly loopback (127.0.0.1, localhost, ::1).
- Outbound network calls to external hosts are forbidden (raises ValueError).
- Zero API keys, zero cloud calls, zero external internet dependencies.
- Retries once on timeout, bad JSON, or schema mismatch; then returns None.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


def _load_env_file() -> None:
    """Best-effort loading of root .env configuration."""
    root_env = Path(__file__).resolve().parents[3] / ".env"
    if root_env.is_file():
        try:
            for raw_line in root_env.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
        except Exception:
            pass


_load_env_file()

# Environment defaults per Phase 15 specification
DEFAULT_AGENT_MODE = os.environ.get("APSLA_AGENT_MODE", "off").lower()
DEFAULT_LOCAL_URL = os.environ.get("APSLA_LOCAL_URL", "http://127.0.0.1:11434")
DEFAULT_LOCAL_MODEL = os.environ.get("APSLA_LOCAL_MODEL", "qwen2.5-coder:3b")
DEFAULT_MAX_STEPS = int(os.environ.get("APSLA_AGENT_MAX_STEPS", "12"))
DEFAULT_MAX_LLM_CALLS = int(os.environ.get("APSLA_AGENT_MAX_LLM_CALLS", "8"))
DEFAULT_TIMEOUT_S = float(os.environ.get("APSLA_AGENT_TIMEOUT_S", "60.0"))

ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def validate_loopback_url(url: str) -> str:
    """Validate that the URL host is strictly loopback (127.0.0.1, localhost, or ::1).

    Raises:
        ValueError: If host is external, maintaining 'outbound network calls: 0'.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().strip("[]")
    if not host or host not in ALLOWED_HOSTS:
        raise ValueError(
            f"Security violation: APSLA_LOCAL_URL host must be strictly 127.0.0.1, "
            f"localhost, or ::1 (got '{host}'). Outbound network calls are prohibited."
        )
    return url


def validate_schema(data: Any, schema: dict[str, Any]) -> bool:
    """Hermetic schema validator without external dependencies."""
    if not isinstance(schema, dict):
        return True

    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(data, dict):
            return False
        # Required properties
        for req in schema.get("required", []):
            if req not in data:
                return False
        # Validate properties
        props = schema.get("properties", {})
        return all(not (k in props and not validate_schema(v, props[k])) for k, v in data.items())

    if expected_type == "array":
        if not isinstance(data, list):
            return False
        item_schema = schema.get("items")
        if item_schema and isinstance(item_schema, dict):
            for item in data:
                if not validate_schema(item, item_schema):
                    return False
        return True

    if expected_type == "string":
        if not isinstance(data, str):
            return False
        return not ("enum" in schema and data not in schema["enum"])

    if expected_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            return False
        return not ("enum" in schema and data not in schema["enum"])

    if expected_type == "number":
        return not (not isinstance(data, (int, float)) or isinstance(data, bool))

    if expected_type == "boolean":
        return isinstance(data, bool)

    return not ("enum" in schema and data not in schema["enum"])


class LocalLLM:
    """Local Ollama client communicating exclusively over loopback HTTP."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 20.0,
    ) -> None:
        raw_url = (base_url or os.environ.get("APSLA_LOCAL_URL", DEFAULT_LOCAL_URL)).rstrip("/")
        self.base_url = validate_loopback_url(raw_url)
        requested = model or os.environ.get("APSLA_LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
        if model:
            self.model = model
        elif transport is not None:
            self.model = requested
        else:
            try:
                status_data = get_agent_status()
                installed = status_data.get("models", [])
                if requested in installed:
                    self.model = requested
                elif status_data.get("model") and status_data.get("model") in installed:
                    self.model = str(status_data["model"])
                elif installed:
                    self.model = installed[0]
                else:
                    self.model = requested
            except Exception:
                self.model = requested
        self.transport = transport
        self.timeout = timeout
        self.call_count = 0

    def chat_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Call Ollama /api/chat expecting structured JSON matching schema.

        Retries once on timeout, invalid JSON, or schema violation.
        Returns dict on success, None on failure.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": "json",
            "options": {
                "temperature": 0,
                "seed": 42,
                "num_predict": 200,
                "num_ctx": 4096,
            },
            "stream": False,
        }

        # Up to 2 attempts (1 initial + 1 retry)
        for _attempt in range(2):
            self.call_count += 1
            try:
                with httpx.Client(
                    base_url=self.base_url,
                    transport=self.transport,
                    timeout=self.timeout,
                ) as client:
                    resp = client.post("/api/chat", json=payload)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()

                    # Ollama chat response structure
                    content = ""
                    if "message" in data and isinstance(data["message"], dict):
                        content = data["message"].get("content", "")
                    elif "response" in data:
                        content = data.get("response", "")

                    if not content:
                        continue

                    parsed = json.loads(content)
                    if not isinstance(parsed, dict):
                        continue

                    if schema and not validate_schema(parsed, schema):
                        continue

                    return parsed
            except (httpx.TimeoutException, httpx.RequestError, json.JSONDecodeError, Exception):
                continue

        return None


LocalOllamaClient = LocalLLM


def get_agent_status(
    transport: httpx.BaseTransport | None = None,
    override_mode: str | None = None,
) -> dict[str, Any]:
    """Retrieve current agent system status and local model availability.

    Returns:
        dict with {mode, ollama_reachable, model, model_present, fallback_active, message}
    """
    mode = (override_mode or os.environ.get("APSLA_AGENT_MODE", "off")).lower()
    if mode not in {"off", "rules", "local"}:
        mode = "off"

    url = os.environ.get("APSLA_LOCAL_URL", DEFAULT_LOCAL_URL).rstrip("/")
    try:
        validated_url = validate_loopback_url(url)
    except ValueError as e:
        return {
            "mode": mode,
            "ollama_reachable": False,
            "model": os.environ.get("OLLAMA_MODEL", os.environ.get("APSLA_LOCAL_MODEL", DEFAULT_LOCAL_MODEL)),
            "model_present": False,
            "models": [],
            "fallback_active": mode != "off",
            "message": str(e),
        }

    model_name = os.environ.get("OLLAMA_MODEL", os.environ.get("APSLA_LOCAL_MODEL", DEFAULT_LOCAL_MODEL))
    requested_model = model_name
    reachable = False
    present = False
    models: list[str] = []
    message = ""

    try:
        with httpx.Client(base_url=validated_url, transport=transport, timeout=2.0) as client:
            resp = client.get("/api/tags")
            if resp.status_code == 200:
                reachable = True
                tags_data = resp.json()
                models = [
                    m.get("name", "") for m in tags_data.get("models", []) if isinstance(m, dict)
                ]
                models = [model for model in models if model]
                # Prefer the configured exact tag, but when it is absent bind to an
                # actually installed tag from the same model family. Returning the
                # installed tag prevents the provider from sending a nonexistent tag.
                exact = next(
                    (tag for tag in models if tag in {requested_model, f"{requested_model}:latest"}),
                    None,
                )
                family = requested_model.split(":", 1)[0]
                compatible = next(
                    (tag for tag in sorted(models) if tag == family or tag.startswith(f"{family}:")),
                    None,
                )
                matched_model = exact or compatible
                present = matched_model is not None
                if matched_model:
                    model_name = matched_model
                if not present:
                    message = f"Model unavailable. Run: ollama pull {requested_model}"
    except Exception:
        reachable = False
        message = f"Ollama is not running at {validated_url}"

    fallback_active = False
    if mode == "local":
        fallback_active = not (reachable and present)
    elif mode == "rules":
        fallback_active = False  # Rules is intentional, not fallback

    return {
        "mode": mode,
        "ollama_reachable": reachable,
        "model": model_name,
        "model_present": present,
        "models": models,
        "fallback_active": fallback_active,
        "message": message,
    }
