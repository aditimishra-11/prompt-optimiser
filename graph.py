from langgraph.graph import StateGraph, END
from state.schema import PromptOptimiserState
from nodes.run_prompt import run_prompt_node
from nodes.score_output import score_output_node
from nodes.analyse_weakness import analyse_weakness_node
from nodes.rewrite_prompt import rewrite_prompt_node
from nodes.convergence import convergence_node, should_continue


def build_graph() -> StateGraph:
    g = StateGraph(PromptOptimiserState)

    g.add_node("run_prompt", run_prompt_node)
    g.add_node("score_output", score_output_node)
    g.add_node("analyse_weakness", analyse_weakness_node)
    g.add_node("rewrite_prompt", rewrite_prompt_node)
    g.add_node("convergence", convergence_node)

    g.set_entry_point("run_prompt")
    g.add_edge("run_prompt", "score_output")
    g.add_edge("score_output", "analyse_weakness")
    g.add_edge("analyse_weakness", "rewrite_prompt")
    g.add_edge("rewrite_prompt", "convergence")
    g.add_conditional_edges(
        "convergence",
        should_continue,
        {"continue": "run_prompt", "end": END},
    )

    return g.compile()
