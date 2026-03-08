# app/core/evaluator.py
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, Tuple

import pandas as pd
from sympy import Symbol, simplify, sympify

from app.core.config import CORRECT_THRESHOLD


def _normalize(expr: str) -> str:
    # Common small normalizations for model outputs
    if expr is None:
        return ""
    s = str(expr).strip()
    # Standardize equality tokens
    s = s.replace("==", "=")
    # Caret to Python power
    s = s.replace("^", "**")
    # Strip code fences if present
    if s.startswith("```"):
        s = s.strip("`").strip()
    return s


def _is_equation_form(a: str, b: str) -> bool:
    return ("=" in a) and ("=" in b)


def _free_symbols_from(*exprs) -> Iterable[Symbol]:
    syms = set()
    for e in exprs:
        try:
            syms |= set(sympify(e).free_symbols)
        except Exception:
            pass
    return sorted(list(syms), key=lambda x: x.name)


@dataclass
class EvalResult:
    score: float
    exact: bool
    details: str = ""


def evaluate_math(
    ai_expr: str,
    correct_expr: str,
    *,
    samples: int = 8,
    tol: float = 1e-6,
    sample_range: Tuple[int, int] = (-5, 5),
) -> EvalResult:
    """
    Evaluate AI expression vs. correct expression.

    - Tries exact symbolic equality first (score 1.0 if equal)
    - If not equal, samples numeric assignments and computes a fraction match

    Supports expressions and simple equation forms like "x=2".
    """

    a = _normalize(ai_expr)
    c = _normalize(correct_expr)

    if not a or not c:
        return EvalResult(score=0.0, exact=False, details="Empty expression")

    try:
        if _is_equation_form(a, c):
            a_left, a_right = [x.strip() for x in a.split("=", 1)]
            c_left, c_right = [x.strip() for x in c.split("=", 1)]
            a_diff = simplify(sympify(a_left) - sympify(a_right))
            c_diff = simplify(sympify(c_left) - sympify(c_right))

            # Exact symbolic equivalence of differences
            if simplify(a_diff - c_diff) == 0:
                return EvalResult(score=1.0, exact=True, details="Exact equation match")

            syms = _free_symbols_from(a_diff, c_diff)
            if not syms:
                # No symbols: numeric compare
                try:
                    va = float(a_diff)
                    vc = float(c_diff)
                    return EvalResult(
                        score=1.0 if abs(va - vc) <= tol else 0.0,
                        exact=False,
                        details="Constant equation diff compare",
                    )
                except Exception:
                    return EvalResult(score=0.0, exact=False, details="Failed constant compare")

            hits = 0
            attempts = 0
            low, high = sample_range
            for _ in range(max(samples, 1)):
                subs = {s: random.randint(low, high) for s in syms}
                try:
                    va = float(a_diff.subs(subs))
                    vc = float(c_diff.subs(subs))
                    if math.isfinite(va) and math.isfinite(vc) and abs(va - vc) <= tol:
                        hits += 1
                    attempts += 1
                except Exception:
                    # skip point
                    continue

            score = (hits / attempts) if attempts else 0.0
            return EvalResult(score=score, exact=False, details=f"Equation sampled: {hits}/{attempts}")

        # Pure expression path
        a_val = simplify(sympify(a))
        c_val = simplify(sympify(c))

        if simplify(a_val - c_val) == 0:
            return EvalResult(score=1.0, exact=True, details="Exact expression match")

        syms = _free_symbols_from(a_val, c_val)
        if not syms:
            try:
                va = float(a_val)
                vc = float(c_val)
                return EvalResult(
                    score=1.0 if abs(va - vc) <= tol else 0.0,
                    exact=False,
                    details="Constant expression compare",
                )
            except Exception:
                return EvalResult(score=0.0, exact=False, details="Failed constant compare")

        hits = 0
        attempts = 0
        low, high = sample_range
        for _ in range(max(samples, 1)):
            subs = {s: random.randint(low, high) for s in syms}
            try:
                va = float(a_val.subs(subs))
                vc = float(c_val.subs(subs))
                if math.isfinite(va) and math.isfinite(vc) and abs(va - vc) <= tol:
                    hits += 1
                attempts += 1
            except Exception:
                continue

        score = (hits / attempts) if attempts else 0.0
        return EvalResult(score=score, exact=False, details=f"Expression sampled: {hits}/{attempts}")

    except Exception as e:
        return EvalResult(score=0.0, exact=False, details=f"Parse/compare error: {type(e).__name__}")


def evaluate_dataframe(
    df: pd.DataFrame,
    *,
    ai_col: str = "ai_response",
    correct_col: str = "correct_answer",
    samples: int = 8,
    tol: float = 1e-6,
) -> pd.DataFrame:
    """Apply evaluation to a DataFrame and add score columns."""

    def _apply(row: pd.Series) -> float:
        res = evaluate_math(row[ai_col], row[correct_col], samples=samples, tol=tol)
        return res.score

    out = df.copy()
    out["score"] = out.apply(_apply, axis=1)
    out["is_correct"] = out["score"].apply(
        lambda x: "OK" if x >= CORRECT_THRESHOLD else "X"
    )
    return out

