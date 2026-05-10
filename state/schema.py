from typing import TypedDict


class PromptOptimiserState(TypedDict):
    task_description: str
    rubric: dict                # scoring dimensions + weights
    test_cases: list[dict]      # {input, expected_output} pairs
    current_prompt: str
    current_score: float
    best_prompt: str
    best_score: float
    score_history: list[float]
    weakness_log: list[str]     # one entry per iteration
    outputs: list[dict]         # raw LLM outputs this iteration
    iteration: int
    converged: bool
