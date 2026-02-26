"""One-provider LLM wrapper (MVP)."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMClient:
    provider: str
    model: str
    api_key: Optional[str] = None

    def generate(self, prompt: str) -> str:
        """Replace with actual provider SDK call."""
        return "[LLM STUB] Replace with real LLM provider call."
