# Prompt Optimiser

An autonomous LangGraph agent that iterates on a prompt until it converges on the best version — no human input after kick-off.

Given a task description, a rubric, and a seed prompt, it:
1. Runs the prompt against test cases in parallel
2. Scores outputs with an LLM judge
3. Diagnoses weaknesses
4. Rewrites the prompt
5. Repeats until convergence

---

## How it works

```
seed prompt
    │
    ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌─────────────┐
│  run_prompt  │────▶│ score_output│────▶│ analyse_weakness │────▶│ rewrite_prompt │────▶│ convergence │
└─────────────┘     └─────────────┘     └──────────────────┘     └────────────────┘     └──────┬──────┘
        ▲                                                                                        │
        └───────────────────────────── loop until converged ────────────────────────────────────┘
```

Convergence stops when any of these are true:
- Score ≥ 9.2 (target quality hit)
- 20 iterations reached (hard cap)
- Score plateau — max − min of last 3 scores < 0.3

---

## Stack

| Component | Tool |
|---|---|
| Agent orchestration | LangGraph (StateGraph) |
| Generator (cheap) | gpt-4o-mini |
| Judge + Rewriter (strong) | gpt-4o |
| Tracing | LangSmith |
| Persistence | Supabase (postgres + pgvector) |
| Dashboard | Streamlit |

---

## Setup

```bash
git clone https://github.com/aditimishra-11/prompt-optimiser.git
cd prompt-optimiser
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
```

### Environment variables

```
OPENAI_API_KEY=
LANGCHAIN_API_KEY=        # LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=prompt-optimiser
SUPABASE_URL=
SUPABASE_KEY=
```

### Database

Run `db/schema.sql` against your Supabase project to create the `runs` table.

---

## Usage

```bash
python main.py \
  --task "write a PM STAR story from bullet points" \
  --rubric rubrics/star_story.json \
  --test-cases test_cases/star_story.json \
  --seed-prompt "Given these bullet points, write a STAR story."
```

Each iteration prints the current score. On convergence, the best prompt and score are printed and the full run log is saved to `runs/`.

---

## Dashboard

```bash
streamlit run dashboard.py
```

Shows:
- Score curve across iterations
- Best prompt
- Side-by-side diff of seed vs best prompt
- Per-dimension score breakdown

---

## Rubric format

```json
{
  "task": "description of what the prompt is trying to do",
  "dimensions": [
    { "name": "specificity",    "description": "...", "weight": 0.4 },
    { "name": "impact_clarity", "description": "...", "weight": 0.3 },
    { "name": "structure",      "description": "...", "weight": 0.2 },
    { "name": "conciseness",    "description": "...", "weight": 0.1 }
  ]
}
```

## Test case format

```json
[
  {
    "id": "tc_001",
    "input": "user input to pass to the prompt",
    "expected_output": "what a perfect output looks like",
    "tags": ["edge_case", "vague"]
  }
]
```

Write at least 8 test cases. Diversity matters more than quantity — include vague, technical, short, ambiguous, and ideal inputs.

---

## Project structure

```
prompt-optimiser/
├── main.py                   # CLI entry point
├── graph.py                  # LangGraph assembly
├── dashboard.py              # Streamlit dashboard
├── state/
│   └── schema.py             # PromptOptimiserState TypedDict
├── nodes/
│   ├── run_prompt.py         # Run prompt on test cases (parallel)
│   ├── score_output.py       # LLM-as-judge scoring
│   ├── analyse_weakness.py   # Root cause diagnosis
│   ├── rewrite_prompt.py     # Prompt rewrite
│   └── convergence.py        # Exit check + router
├── rubrics/                  # Example rubrics
├── test_cases/               # Example test cases
├── db/
│   └── schema.sql            # Supabase table definitions
└── runs/                     # Auto-generated run logs (gitignored)
```
