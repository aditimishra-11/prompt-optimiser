from langchain_openai import ChatOpenAI
from state.schema import PromptOptimiserState

_llm = ChatOpenAI(model="gpt-4o", temperature=0.4)


def rewrite_prompt_node(state: PromptOptimiserState) -> dict:
    history_lines = []
    score_hist = state["score_history"]
    weakness_log = state["weakness_log"]

    # Build full triplet history: prompt snapshots aren't stored, so we use
    # score + weakness pairs from all prior iterations
    for i, (score, weakness) in enumerate(zip(score_hist, weakness_log)):
        history_lines.append(
            f"Iteration {i+1}: score={score:.2f} | weakness={weakness}"
        )
    history_text = "\n".join(history_lines) if history_lines else "No prior iterations."

    dims = state["rubric"]["dimensions"]
    dim_text = "\n".join(
        f"- {d['name']} (weight {d['weight']}): {d['description']}" for d in dims
    )

    prompt = f"""You are an expert prompt engineer. Rewrite the prompt below to fix its diagnosed weakness.

Task: {state['task_description']}

Rubric dimensions:
{dim_text}

Current prompt (score {state['current_score']:.2f}/10):
{state['current_prompt']}

Most recent weakness:
{state['weakness_log'][-1]}

Full iteration history (do not repeat failed fixes):
{history_text}

Rules:
- Return ONLY the rewritten prompt text, no commentary.
- Address the specific weakness without breaking what already works.
- Do not make the prompt longer than necessary.
- The prompt will be used as a system message; write it in that voice."""

    response = _llm.invoke([{"role": "user", "content": prompt}])
    new_prompt = response.content.strip()

    return {
        "current_prompt": new_prompt,
        "iteration": state["iteration"] + 1,
    }
