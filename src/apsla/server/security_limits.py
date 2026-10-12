"""Small, process-local request guards used by the local API."""

from __future__ import annotations

import re
import time
import unicodedata
from collections import defaultdict, deque

MAX_REQUEST_BYTES = 1024 * 1024
MAX_TOKENS_PER_FILE = 100_000
MAX_FINDINGS_PER_FILE = 2_000
MAX_AST_NODES = 2_000
MAX_CONCURRENT_EXPENSIVE_REQUESTS = 4
RATE_LIMITS = {"analysis": (20, 60.0), "ai": (8, 60.0), "safety": (5, 60.0)}
_requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def request_group(path: str) -> str | None:
    if path.startswith(("/api/analyze", "/api/fixes/")) or path in {"/api/fix", "/api/fix-all"}:
        return "analysis"
    if path.startswith(("/api/ai/", "/api/llm/")):
        return "ai"
    if path.startswith("/api/agent-safety/"):
        return "safety"
    return None


def rate_allowed(client: str, group: str, now: float | None = None) -> bool:
    limit, period = RATE_LIMITS[group]
    current = time.monotonic() if now is None else now
    bucket = _requests[(client, group)]
    while bucket and current - bucket[0] >= period:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(current)
    return True


def clear_rate_state() -> None:
    _requests.clear()


def safe_filename_label(value: str, fallback: str = "source") -> str:
    """Treat client filenames as labels, never filesystem paths."""
    leaf = value.replace("\\", "/").rsplit("/", 1)[-1]
    label = re.sub(r"[^A-Za-z0-9._-]", "_", leaf).strip("._")[:120]
    return label or fallback


def neutralize_controls(value: str) -> str:
    """Make copied/exported untrusted text inert in terminals and logs."""
    return "".join(
        ch for ch in value if ch in "\n\r\t" or unicodedata.category(ch) not in {"Cc", "Cf", "Cs"}
    )
