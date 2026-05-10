import argparse
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from graph import build_graph


def main():
    parser = argparse.ArgumentParser(description="Prompt Optimiser Agent")
    parser.add_argument("--task", required=True, help="Task description")
    parser.add_argument("--rubric", required=True, help="Path to rubric JSON")
    parser.add_argument("--test-cases", required=True, help="Path to test cases JSON")
    parser.add_argument("--seed-prompt", required=True, help="Initial prompt to optimise")
    args = parser.parse_args()

    rubric = json.loads(Path(args.rubric).read_text())
    test_cases = json.loads(Path(args.test_cases).read_text())

    initial_state = {
        "task_description": args.task,
        "rubric": rubric,
        "test_cases": test_cases,
        "current_prompt": args.seed_prompt,
        "current_score": 0.0,
        "best_prompt": args.seed_prompt,
        "best_score": 0.0,
        "score_history": [],
        "weakness_log": [],
        "outputs": [],
        "iteration": 0,
        "converged": False,
    }

    run_id = str(uuid.uuid4())[:8]
    print(f"\n=== Prompt Optimiser | run {run_id} ===\n")

    graph = build_graph()
    accumulated = dict(initial_state)
    accumulated["seed_prompt"] = args.seed_prompt

    for step in graph.stream(initial_state, config={"recursion_limit": 150}):
        node_name = list(step.keys())[0]
        node_out = step[node_name]
        accumulated.update(node_out)

        if "current_score" in node_out:
            print(f"[iter {accumulated['iteration']}] score={accumulated['current_score']:.3f}")

        if "converged" in node_out and node_out["converged"]:
            print("\nConverged.")

    # Save run log
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    log_path = runs_dir / f"{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(accumulated, indent=2, default=str))

    print(f"\nBest score : {accumulated['best_score']:.3f}")
    print(f"Best prompt:\n{accumulated['best_prompt']}")
    print(f"\nRun log saved to {log_path}")


if __name__ == "__main__":
    main()
