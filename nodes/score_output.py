import asyncio
import json
from langchain_openai import ChatOpenAI
from state.schema import PromptOptimiserState

_llm = ChatOpenAI(model="gpt-4o", temperature=0)


def _build_judge_prompt(rubric: dict, output_item: dict) -> str:
    dims = rubric["dimensions"]
    dim_text = "\n".join(
        f"- {d['name']} (weight {d['weight']}): {d['description']}" for d in dims
    )
    calibration = rubric.get("scoring_calibration", "")
    calibration_line = f"\nScoring calibration: {calibration}\n" if calibration else ""
    return f"""You are a strict output quality judge.{calibration_line}
Task: {rubric['task']}

Scoring dimensions:
{dim_text}

Input given to the model:
{output_item['input']}

Model output:
{output_item['output']}

Expected output (if provided):
{output_item.get('expected_output', 'N/A')}

Score each dimension 1-10. Return JSON only:
{{
  "scores": {{{", ".join(f'"{d["name"]}": <1-10>' for d in dims)}}},
  "reasoning": "<one sentence per dimension>"
}}"""


async def _score_single(rubric: dict, item: dict) -> dict:
    dims = rubric["dimensions"]
    prompt = _build_judge_prompt(rubric, item)
    response = await _llm.ainvoke([{"role": "user", "content": prompt}])
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        data = {"scores": {d["name"]: 5 for d in dims}, "reasoning": "parse error"}
    return {"id": item["id"], **data}


def score_output_node(state: PromptOptimiserState) -> dict:
    rubric = state["rubric"]
    dims = rubric["dimensions"]

    async def _score_all():
        return await asyncio.gather(*[_score_single(rubric, item) for item in state["outputs"]])

    all_breakdowns = asyncio.run(_score_all())

    total_score = 0.0
    for breakdown in all_breakdowns:
        case_score = sum(
            breakdown["scores"].get(d["name"], 5) * d["weight"] for d in dims
        )
        total_score += case_score
    current_score = round(total_score / len(all_breakdowns), 3)

    best_prompt = state["best_prompt"]
    best_score = state["best_score"]
    if current_score > best_score:
        best_prompt = state["current_prompt"]
        best_score = current_score

    return {
        "current_score": current_score,
        "best_prompt": best_prompt,
        "best_score": best_score,
        "score_history": state["score_history"] + [current_score],
        "outputs": [
            {**o, "breakdown": b}
            for o, b in zip(state["outputs"], all_breakdowns)
        ],
    }
