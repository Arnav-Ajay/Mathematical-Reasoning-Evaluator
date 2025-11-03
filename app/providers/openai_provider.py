from __future__ import annotations

import os
from typing import Optional

from .base import MathProvider, ProviderResponse


class OpenAIProvider(MathProvider):
    name = "openai"

    def __init__(self) -> None:
        self._ready = bool(os.getenv("OPENAI_API_KEY"))
        self._client = None
        if self._ready:
            try:
                from openai import OpenAI  # type: ignore

                self._client = OpenAI()
            except Exception:
                self._ready = False

    def available(self) -> bool:
        return self._ready and self._client is not None

    @staticmethod
    def default_models() -> list[str]:
        # Safe default small models suitable for PoC math
        return [
            "gpt-4o-mini",
            "o4-mini",
        ]

    def generate(self, *, model: str, prompt: str) -> ProviderResponse:
        if not self.available():
            return ProviderResponse(model=model, output="", error="OpenAI not available")

        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise math solver. Return only the final"
                            " SymPy-compatible expression or equation. No prose."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0,
            )
            content = resp.choices[0].message.content.strip()
            # Strip code fences if the model used them
            if content.startswith("```"):
                content = content.strip("`").strip()
            return ProviderResponse(model=model, output=content)
        except Exception as e:
            return ProviderResponse(model=model, output="", error=str(e))

