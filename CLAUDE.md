# Prompt Optimiser Agent

## What this project does
An autonomous LangGraph agent that takes a task description, a rubric,
and a seed prompt — then iterates on the prompt by running it against
test cases, scoring outputs with an LLM judge, diagnosing weaknesses,
and rewriting the prompt. Loops until convergence. No human input
after the initial kick-off.

---

## Stack
- Agent orchestration: LangGraph (StateGraph)
- LLM execution (cheap): gpt-4o-mini
- LLM judge + rewriter (strong): gpt-4o
- Tracing: LangSmith
- Persistence: Supabase (postgres + pgvector)
- Dashboard: Streamlit
- Async: asyncio.gather for parallel test case runs
- Config: python-dotenv

---

## Project structure
prompt-optimiser/
├── CLAUDE.md
├── .env.example
├── requirements.txt
├── main.py                   # CLI entry point
├── graph.py                  # LangGraph assembly
├── state/
│   └── schema.py             # PromptOptimiserState TypedDict
├── nodes/
│   ├── run_prompt.py         # Node 1: run prompt on test cases
│   ├── score_output.py       # Node 2: LLM-as-judge scoring
│   ├── analyse_weakness.py   # Node 3: root cause diagnosis
│   ├── rewrite_prompt.py     # Node 4: prompt rewrite
│   └── convergence.py        # Node 5: exit check + router
├── rubrics/
│   └── star_story.json       # Example rubric
├── test_cases/
│   └── star_story.json       # 8 diverse test cases
├── runs/                     # Auto-generated run logs (JSON)
├── db/
│   └── schema.sql            # Supabase table definitions
└── dashboard.py              # Streamlit score curve + diff view

---

## State schema (PromptOptimiserState TypedDict)
- task_description: str
- rubric: dict               # scoring dimensions + weights
- test_cases: list[dict]     # {input, expected_output} pairs
- current_prompt: str
- current_score: float
- best_prompt: str
- best_score: float
- score_history: list[float]
- weakness_log: list[str]    # one entry per iteration
- outputs: list[dict]        # raw LLM outputs this iteration
- iteration: int
- converged: bool

---

## Convergence rules
Stop the loop when ANY of these are true:
1. current_score >= 9.2       (target quality hit)
2. iteration >= 20            (hard cap)
3. max(last 3 scores) - min(last 3 scores) < 0.3   (plateau)

Always update best_prompt and best_score before checking convergence.
If a later iteration regresses, best_prompt must still hold the peak.

---

## LLM model assignments
- run_prompt node:        gpt-4o-mini  (called N times per iter, keep cheap)
- score_output node:      gpt-4o       (judge must be stronger than generator)
- analyse_weakness node:  gpt-4o       (diagnosis needs reasoning quality)
- rewrite_prompt node:    gpt-4o       (rewrite is the most critical call)

---

## Rubric format (JSON)
{
  "task": "description of what the prompt is trying to do",
  "dimensions": [
    {
      "name": "specificity",
      "description": "are outputs specific with concrete examples?",
      "weight": 0.4
    },
    {
      "name": "impact_clarity",
      "description": "is the impact/outcome clearly stated?",
      "weight": 0.3
    },
    {
      "name": "structure",
      "description": "does the output follow the expected format?",
      "weight": 0.2
    },
    {
      "name": "conciseness",
      "description": "is the output free of padding and filler?",
      "weight": 0.1
    }
  ]
}

---

## Test case format (JSON)
[
  {
    "id": "tc_001",
    "input": "the user input to pass to the prompt",
    "expected_output": "optional — what a perfect output looks like",
    "tags": ["edge_case", "vague"]
  }
]
Write 8 test cases minimum. Include: vague input, very technical input,
short input, ambiguous input, ideal input. Diversity matters more than
quantity — 8 varied cases beats 20 similar ones.

---

## Supabase schema (runs table)
CREATE TABLE runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text NOT NULL,
  iteration int NOT NULL,
  prompt text NOT NULL,
  score float NOT NULL,
  score_breakdown jsonb,
  weakness text,
  rewritten_prompt text,
  converged boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

---

## Key behaviours to implement
1. The weakness analyser must receive the FULL weakness_log so it never
   repeats a fix that was already tried and failed.
2. The rewriter must receive the full triplet history
   (prompt → score → weakness) for every prior iteration.
3. Run all test cases in parallel using asyncio.gather — not sequentially.
4. Save every iteration to Supabase immediately after convergence check,
   not at the end of the full run.
5. The Streamlit dashboard shows: score curve, best_prompt, side-by-side
   diff of seed prompt vs best prompt, per-dimension breakdown table.

---

## Environment variables (.env)
OPENAI_API_KEY=
LANGCHAIN_API_KEY=          # LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=prompt-optimiser
SUPABASE_URL=
SUPABASE_KEY=

---

## CLI usage (main.py)
python main.py \
  --task "write a PM STAR story from bullet points" \
  --rubric rubrics/star_story.json \
  --test-cases test_cases/star_story.json \
  --seed-prompt "Given these bullet points, write a STAR story."

---

## First task to build toward
Task: given bullet points about a project, write a PM-style STAR story
(Situation, Task, Action, Result) suitable for a job interview.
Rubric dimensions: specificity, impact clarity, structure, conciseness.
This is a good first task because: outputs are short (easy to judge),
quality differences are obvious, and it is directly useful.
