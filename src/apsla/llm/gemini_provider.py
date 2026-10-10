"""Google Gemini LLM provider implementation using httpx."""

from __future__ import annotations

import json
import logging
import os

import httpx

from apsla.llm.provider import LLMProvider, truncate_context_lines
from apsla.models import Edit, Finding, Fix, Range, VerificationResult

logger = logging.getLogger("apsla.llm.gemini")


class GeminiProvider(LLMProvider):
    """Google Gemini API integration for remediation and explanations."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.transport = transport
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.timeout = 15.0

    def is_configured(self) -> bool:
        """Check if valid Gemini API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    @property
    def provider_name(self) -> str:
        return "gemini"

    def suggest_fix(self, source: str, finding: Finding) -> list[Fix]:
        """Request fix suggestion from Gemini API."""
        if not self.is_configured():
            return []

        snippet, start_line, end_line = truncate_context_lines(
            source, finding.range.start_line, max_lines=200
        )

        prompt = (
            f"You are a code security assistant. Fix the following vulnerability.\n"
            f"Rule: {finding.rule_id} ({finding.cwe}): {finding.title}\n"
            f"Location: Line {finding.range.start_line}, Col {finding.range.start_col}\n"
            f"Source snippet (lines {start_line}-{end_line}):\n```\n{snippet}\n```\n"
            f"Return ONLY a JSON object with keys: title, description, start_line, start_col, end_line, end_col, new_text."
        )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        params = {"key": self.api_key}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }

        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                resp = client.post(url, params=params, json=payload)
                if resp.status_code != 200:
                    logger.warning("Gemini API returned status %d", resp.status_code)
                    return []
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return []
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return self._parse_fix_response(text, finding)
        except Exception as exc:
            logger.warning("Gemini request failed: %s", type(exc).__name__)
            return []

    def explain(self, finding: Finding) -> str:
        """Request explanation from Gemini API."""
        if not self.is_configured():
            return ""

        prompt = (
            f"Explain this vulnerability in plain English:\n"
            f"Rule: {finding.rule_id} ({finding.cwe})\n"
            f"Title: {finding.title}\n"
            f"Message: {finding.message}\n"
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        params = {"key": self.api_key}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                resp = client.post(url, params=params, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return str(
                            candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        )
        except Exception as exc:
            logger.warning("Gemini explain failed: %s", type(exc).__name__)
        return ""

    def _parse_fix_response(self, text: str, finding: Finding) -> list[Fix]:
        """Extract JSON fix payload and construct Fix instance."""
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]
            clean = clean.strip()

        try:
            parsed = json.loads(clean)
        except Exception:
            return []

        title = parsed.get("title", f"AI Fix for {finding.rule_id}")
        desc = parsed.get("description", "Proposed automated fix from Gemini AI.")
        new_text = parsed.get("new_text") or parsed.get("replacement") or ""
        start_line = int(parsed.get("start_line", finding.range.start_line))
        start_col = int(parsed.get("start_col", finding.range.start_col))
        end_line = int(parsed.get("end_line", finding.range.end_line))
        end_col = int(parsed.get("end_col", finding.range.end_col))

        edits = [
            Edit(
                range=Range(
                    start_line=start_line, start_col=start_col, end_line=end_line, end_col=end_col
                ),
                new_text=new_text,
            )
        ]
        return [
            Fix(
                id=f"LLM-GEMINI-{finding.rule_id}-{finding.range.start_line}",
                finding_id=finding.id,
                title=title,
                description=desc,
                confidence="review",
                kind="llm",
                edits=edits,
                verification=VerificationResult(
                    syntax_ok=True,
                    finding_gone=False,
                    new_findings=[],
                    verified=False,
                    notes="Awaiting shadow verification.",
                ),
            )
        ]
