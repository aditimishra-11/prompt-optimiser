import difflib
import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Prompt Optimiser Dashboard", layout="wide")
st.markdown("""
<style>
pre, code { white-space: pre-wrap !important; word-break: break-word !important; }
</style>
""", unsafe_allow_html=True)
st.title("Prompt Optimiser Dashboard")

runs_dir = Path("runs")
run_files = sorted(runs_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True) if runs_dir.exists() else []

if not run_files:
    st.info("No run logs found in ./runs/. Run main.py first.")
    st.stop()

selected = st.selectbox("Select run", [f.name for f in run_files])
data = json.loads((runs_dir / selected).read_text())

score_history = data.get("score_history", [])
best_prompt = data.get("best_prompt", "")

col1, col2, col3 = st.columns(3)
col1.metric("Best score", f"{data.get('best_score', 0):.3f} / 10")
col2.metric("Iterations", data.get("iteration", 0))
col3.metric("Converged", str(data.get("converged", False)))

st.subheader("Score curve")
if score_history:
    st.line_chart(score_history)
else:
    st.write("No score history.")

seed_prompt = data.get("seed_prompt", "")

st.subheader("Seed prompt")
st.text_area("", value=seed_prompt, height=80, disabled=True, key="seed_prompt_box") if seed_prompt else st.info("Seed prompt not stored in this run log.")

st.subheader("Best prompt")
st.code(best_prompt, language="text")

st.subheader("Seed vs Best — diff")
outputs = data.get("outputs", [])
if outputs and seed_prompt:
    diff = difflib.unified_diff(
        seed_prompt.splitlines(), best_prompt.splitlines(),
        fromfile="seed", tofile="best", lineterm=""
    )
    st.code("\n".join(diff), language="diff")
elif not seed_prompt:
    st.info("Seed prompt not stored in this run log. Re-run to capture it.")

st.subheader("Per-dimension score breakdown (last iteration)")
if outputs and outputs[0].get("breakdown"):
    rows = []
    for item in outputs:
        bd = item.get("breakdown", {})
        scores = bd.get("scores", {})
        rows.append({"test_case": item["id"], **scores})
    st.dataframe(rows)
else:
    st.write("No breakdown data.")

st.subheader("Weakness log")
for i, w in enumerate(data.get("weakness_log", []), 1):
    st.markdown(f"**Iteration {i}:** {w}")
