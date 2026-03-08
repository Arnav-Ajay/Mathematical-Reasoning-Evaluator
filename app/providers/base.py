# app/providers/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderResponse:
    model: str
    output: str
    error: Optional[str] = None


class MathProvider:
    """Base interface for math generation providers."""

    name: str = "base"

    def available(self) -> bool:
        return False

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0,
    ) -> ProviderResponse:
        raise NotImplementedError
