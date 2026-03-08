# app/providers/openai_provider.py
from __future__ import annotations
import os

try:
    from app.core.config import DEFAULT_OPENAI_MODELS, OPENAI_SYSTEM_PROMPT
except ModuleNotFoundError:
    from app.core.config import DEFAULT_OPENAI_MODELS, OPENAI_SYSTEM_PROMPT

from app.providers.base import MathProvider, ProviderResponse


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
        return list(DEFAULT_OPENAI_MODELS)

    def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0,
    ) -> ProviderResponse:
        if not self.available():
            return ProviderResponse(model=model, output="", error="OpenAI not available")

        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt or OPENAI_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=temperature,
            )
            content = resp.choices[0].message.content.strip()
            # Strip code fences if the model used them
            if content.startswith("```"):
                content = content.strip("`").strip()
            return ProviderResponse(model=model, output=content)
        except Exception as e:
            return ProviderResponse(model=model, output="", error=str(e))
