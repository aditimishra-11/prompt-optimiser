from state.schema import PromptOptimiserState


def convergence_node(state: PromptOptimiserState) -> dict:
    score = state["current_score"]
    iteration = state["iteration"]
    history = state["score_history"]

    converged = False

    if score >= 9.2:
        converged = True
    elif iteration >= 20:
        converged = True
    elif len(history) >= 3:
        last3 = history[-3:]
        if max(last3) - min(last3) < 0.15:
            converged = True

    return {"converged": converged}


def should_continue(state: PromptOptimiserState) -> str:
    return "end" if state["converged"] else "continue"
