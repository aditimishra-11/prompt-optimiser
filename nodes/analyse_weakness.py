from langchain_openai import ChatOpenAI
from state.schema import PromptOptimiserState

_llm = ChatOpenAI(model="gpt-4o", temperature=0)


def analyse_weakness_node(state: PromptOptimiserState) -> dict:
    prior_weaknesses = "\n".join(
        f"Iteration {i+1}: {w}" for i, w in enumerate(state["weakness_log"])
    )

    outputs_text = "\n\n".join(
        f"[{o['id']}] Input: {o['input']}\nOutput: {o['output']}\nScores: {o.get('breakdown', {}).get('scores', {})}"
        for o in state["outputs"]
    )

    prompt = f"""You are diagnosing why an LLM prompt is underperforming.

Task: {state['task_description']}
Current prompt:
{state['current_prompt']}

Current score: {state['current_score']} / 10

Outputs this iteration:
{outputs_text}

Previously identified weaknesses (DO NOT repeat these — they were already tried):
{prior_weaknesses if prior_weaknesses else 'None yet.'}

Identify the single most impactful root cause limiting the score right now.
Be specific: name the failure pattern, cite 1-2 examples from the outputs above.
Return 2-3 sentences maximum."""

    response = _llm.invoke([{"role": "user", "content": prompt}])
    weakness = response.content.strip()

    return {"weakness_log": state["weakness_log"] + [weakness]}
