# app/core/schemas.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

@dataclass
class Action:
    problem_id: int
    problem: str
    correct_answer: str


@dataclass
class ResponseSchema:
    ai_response: str
    reasoning: Optional[str] = None
    raw_output: str = ""


@dataclass
class GenerationResult:
    action: Action
    model: str
    response: Optional[ResponseSchema] = None
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    problem_id: int
    problem: str
    ai_response: str
    correct_answer: str
    is_correct: str
    score: float
    model: str
    error: Optional[str] = None
    reasoning: Optional[str] = None
