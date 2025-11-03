from __future__ import annotations

import os
from typing import List, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app.evaluator import evaluate_dataframe
from app.providers import OpenAIProvider, ProviderResponse


load_dotenv(override=False)

st.set_page_config(page_title="Math Reasoning Evaluator", layout="wide")

st.title("🧮 Mathematical Reasoning Evaluator (PoC)")
st.caption(
    "Evaluate AI-generated math outputs using SymPy. Enter a problem and correct answer,"
    " then compare manual or model-generated solutions."
)


@st.cache_data
def _provider_status() -> Tuple[bool, List[str]]:
    openai_provider = OpenAIProvider()
    available = openai_provider.available()
    models = OpenAIProvider.default_models()
    return available, models


def _layout_sidebar():
    st.sidebar.header("Settings")
    st.sidebar.write("API Keys from .env if present.")
    st.sidebar.write("OpenAI available:" if _provider_status()[0] else "OpenAI unavailable.")
    st.sidebar.divider()
    st.sidebar.markdown("Export results with the download button below the table.")


_layout_sidebar()

with st.form("problem_form"):
    st.subheader("1) Enter Problem and Correct Answer")
    problem = st.text_area(
        "Problem (describe what to solve; the prompt for models)",
        value="(x+1)**2",
        height=80,
    )
    correct = st.text_input(
        "Correct Answer (SymPy-compatible expression or equation)", value="x**2 + 2*x + 1"
    )
    samples = st.slider("Partial scoring samples", min_value=1, max_value=20, value=8)
    tol = st.number_input("Tolerance", min_value=1e-9, max_value=1e-3, value=1e-6, format="%.1e")

    submitted = st.form_submit_button("Set Problem Context")

if "entries" not in st.session_state:
    st.session_state.entries = []  # List[Tuple[str, str]] => (label, ai_output)


st.subheader("2) Candidate Solutions")
colA, colB = st.columns(2)
with colA:
    st.markdown("**Manual Entries**")
    if st.button("Add Manual Entry"):
        st.session_state.entries.append((f"manual-{len(st.session_state.entries)+1}", ""))

    to_remove = []
    for idx, (label, content) in enumerate(st.session_state.entries):
        c1, c2 = st.columns([3, 7])
        with c1:
            new_label = st.text_input(f"Label #{idx+1}", value=label, key=f"lbl_{idx}")
        with c2:
            new_content = st.text_input(
                f"AI Response #{idx+1}", value=content, key=f"resp_{idx}"
            )
        st.session_state.entries[idx] = (new_label, new_content)
        if st.button(f"Remove #{idx+1}"):
            to_remove.append(idx)
    for i in reversed(to_remove):
        st.session_state.entries.pop(i)

with colB:
    st.markdown("**Generate via OpenAI (optional)**")
    openai_available, openai_models = _provider_status()
    if not openai_available:
        st.info("OpenAI not available. Set OPENAI_API_KEY in .env to enable.")
    selected_models = st.multiselect(
        "Select OpenAI models",
        options=openai_models,
        default=openai_models[:1] if openai_models else [],
    )
    if st.button("Generate from Selected Models", disabled=not (openai_available and problem.strip())):
        prov = OpenAIProvider()
        prompt = (
            "Solve the following math problem. Return only the final SymPy-compatible"
            " expression or equation (no prose). Problem: "
            + problem.strip()
        )
        outputs: list[ProviderResponse] = []
        for m in selected_models:
            outputs.append(prov.generate(model=m, prompt=prompt))

        # Add to entries (model name and output or error)
        for r in outputs:
            label = f"openai:{r.model}"
            content = r.output if r.output else f"ERROR: {r.error or 'unknown'}"
            st.session_state.entries.append((label, content))


st.subheader("3) Evaluate")
if st.button("Run Evaluation", type="primary"):
    rows = []
    for i, (label, content) in enumerate(st.session_state.entries, start=1):
        rows.append(
            {
                "problem_id": i,
                "provider": label,
                "problem": problem,
                "ai_response": content,
                "correct_answer": correct,
            }
        )

    if not rows:
        st.warning("Add at least one candidate solution (manual or generated).")
    else:
        df = pd.DataFrame(rows)
        scored = evaluate_dataframe(df, ai_col="ai_response", correct_col="correct_answer", samples=int(samples), tol=float(tol))
        st.dataframe(scored, use_container_width=True)

        csv = scored.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="evaluation_results.csv", mime="text/csv")

st.divider()
st.caption(
    "Tip: Use SymPy-compatible syntax (e.g., `**` for power, `diff(3*x**3, x)`)."
)

