# Mathematical Reasoning Evaluator (PoC)

Lightweight evaluator that tests AI-generated math solutions for correctness using SymPy and Pandas. Includes a Streamlit UI for live input and optional integration with OpenAI models to benchmark responses.

## Features

- Symbolic comparison of algebra/calculus expressions and simple equations
- Binary or partial scoring via randomized numeric checks
- Streamlit UI for user-entered problems and answers
- Optional OpenAI integration to generate candidate solutions from selected models
- Export results as CSV

## Quickstart

1) Create a virtual environment (recommended) and install deps

```
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2) (Optional) Configure API keys in `.env`

```
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=...
```

3) Run the Streamlit app

```
streamlit run app/ui_streamlit.py
```

## How Scoring Works

- Exact symbolic equality: Attempts to parse both sides and uses `sympy.simplify` to detect equality.
- Equation handling: Supports `x=2` form by comparing differences (LHS-RHS) symbolically.
- Partial credit: If exact check fails, samples random numeric assignments for free symbols and computes a fraction of points where expressions match within tolerance.

## Example Programmatic Usage

```python
import pandas as pd
from app.evaluator import evaluate_math, evaluate_dataframe

data = [
    {"problem_id": 1, "problem": "(x+1)**2", "ai_response": "x**2 + 2*x + 1", "correct_answer": "x**2 + 2*x + 1"},
    {"problem_id": 2, "problem": "diff(3*x**3, x)", "ai_response": "9*x**2", "correct_answer": "9*x**2"},
    {"problem_id": 3, "problem": "2*x + 4 - 8", "ai_response": "x=3", "correct_answer": "x=2"},
]

df = pd.DataFrame(data)
res = evaluate_dataframe(df, ai_col="ai_response", correct_col="correct_answer")
print(res[["problem_id", "ai_response", "correct_answer", "is_correct", "score"]])
```

Expected output:
```
   problem_id     ai_response    correct_answer is_correct  score
0           1  x**2 + 2*x + 1  x**2 + 2*x + 1          ✅    1.0
1           2          9*x**2          9*x**2          ✅    1.0
2           3              x=3              x=2          ❌    0.0
```

## Notes

- The OpenAI integration is optional and only used if an API key is present.
- Input should be SymPy-compatible where possible (e.g., `^` becomes `**`, `diff(3*x**3, x)`).
- This is a PoC; extend as needed for inequalities, systems, and more robust parsing.
