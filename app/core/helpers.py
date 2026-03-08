# app/core/helpers.py
from __future__ import annotations
import json
from typing import Iterable, Optional

import pandas as pd

from app.core.config import CORRECT_THRESHOLD
from app.core.schemas import Action, ResponseSchema

def normalize_response(raw: str) -> ResponseSchema:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()

    reasoning: Optional[str] = None
    if text.startswith("{") and text.endswith("}"):
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                maybe_answer = payload.get("ai_response") or payload.get("answer") or payload.get("response")
                if maybe_answer is not None:
                    text = str(maybe_answer).strip()
                maybe_reasoning = payload.get("reasoning")
                if maybe_reasoning is not None:
                    reasoning = str(maybe_reasoning).strip() or None
        except Exception:
            pass

    if "\n" in text:
        text = text.splitlines()[0].strip()

    if not text:
        raise ValueError("Model returned empty output.")

    return ResponseSchema(ai_response=text, reasoning=reasoning, raw_output=raw or "")


def build_generation_prompt(problem: str, examples: Optional[Iterable[Action]] = None) -> str:
    lines = [
        "Return only the final SymPy-compatible answer.",
        "No explanation, no steps, no markdown, no code fences.",
        "Use '*' for multiplication and '**' for powers.",
    ]

    if examples:
        lines.append("")
        for i, ex in enumerate(examples, start=1):
            lines.append(f"Example {i}")
            lines.append(f"Problem: {ex.problem}")
            lines.append(f"Answer: {ex.correct_answer}")

    lines.append("")
    lines.append(f"Problem: {problem}")
    lines.append("Answer:")
    return "\n".join(lines)


def format_scored_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["is_correct"] = out["score"].apply(lambda x: "OK" if x >= CORRECT_THRESHOLD else "X")
    return out
