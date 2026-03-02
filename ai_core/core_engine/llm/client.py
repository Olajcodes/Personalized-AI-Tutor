"""LLM client supporting Groq/OpenAI compatible chat completion APIs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


class LLMClientError(RuntimeError):
    pass


@dataclass
class LLMClient:
    provider: str
    model: str
    api_key: Optional[str] = None

    def _resolve_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        if self.provider.lower() == "groq":
            key = os.getenv("GROQ_API_KEY")
            if key:
                return key
        key = os.getenv("LLM_API_KEY")
        if key:
            return key
        raise LLMClientError("No LLM API key configured. Set GROQ_API_KEY or LLM_API_KEY.")

    def _client(self):
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise LLMClientError("openai dependency is required for LLM calls.") from exc

        api_key = self._resolve_api_key()
        provider = self.provider.lower()
        if provider == "groq":
            base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
            return OpenAI(api_key=api_key, base_url=base_url)
        if provider in {"openai", ""}:
            return OpenAI(api_key=api_key)
        raise LLMClientError(f"Unsupported LLM provider: {self.provider}")

    def generate(self, prompt: str) -> str:
        """Generate a completion from configured provider."""
        client = self._client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception as exc:
            raise LLMClientError(f"LLM generation failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMClientError("LLM returned empty content.")
        return str(content).strip()
