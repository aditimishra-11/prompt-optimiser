import asyncio
from langchain_openai import ChatOpenAI
from state.schema import PromptOptimiserState

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


def _format_input(raw_input) -> str:
    if isinstance(raw_input, dict):
        return "\n".join(f"{k}: {v}" for k, v in raw_input.items())
    return str(raw_input)


async def _run_single(prompt: str, test_case: dict) -> dict:
    user_content = _format_input(test_case["input"])
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]
    response = await _llm.ainvoke(messages)
    return {
        "id": test_case["id"],
        "input": user_content,
        "expected_output": test_case.get("expected_output", ""),
        "output": response.content,
        "tags": test_case.get("tags", []),
    }


async def run_prompt_async(state: PromptOptimiserState) -> dict:
    tasks = [_run_single(state["current_prompt"], tc) for tc in state["test_cases"]]
    outputs = await asyncio.gather(*tasks)
    return {"outputs": list(outputs)}


def run_prompt_node(state: PromptOptimiserState) -> dict:
    return asyncio.run(run_prompt_async(state))
