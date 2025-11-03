import pandas as pd
from app.evaluator import evaluate_dataframe


def main():
    data = [
        {"problem_id": 1, "problem": "(x+1)**2", "ai_response": "x**2 + 2*x + 1", "correct_answer": "x**2 + 2*x + 1"},
        {"problem_id": 2, "problem": "diff(3*x**3, x)", "ai_response": "9*x**2", "correct_answer": "9*x**2"},
        {"problem_id": 3, "problem": "2*x + 4 - 8", "ai_response": "x=3", "correct_answer": "x=2"},
    ]

    df = pd.DataFrame(data)
    out = evaluate_dataframe(df, ai_col="ai_response", correct_col="correct_answer")
    print(out[["problem_id", "ai_response", "correct_answer", "is_correct", "score"]])


if __name__ == "__main__":
    main()

