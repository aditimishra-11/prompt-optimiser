# Prompt Optimiser Agent

An autonomous LangGraph agent that finds the best prompt for any task — by running a seed prompt against test cases, scoring outputs with an LLM judge, diagnosing weaknesses, and rewriting the prompt iteratively until it converges.

You run it once per use case. It hands you a prompt. You use that prompt in Claude or ChatGPT for your daily work.

---

## How it works

```
seed prompt → run on test cases → score → diagnose weakness → rewrite → loop → best prompt
```

The agent runs autonomously until one of three conditions is met:
- Score reaches the target threshold (default 9.2/10)
- Score plateaus — less than 0.15 improvement over 3 consecutive iterations
- Maximum iterations reached (default 20)

---

## Project structure

```
prompt-optimiser/
├── CLAUDE.md                        # Persistent context for Claude Code sessions
├── main.py                          # CLI entry point
├── graph.py                         # LangGraph state machine assembly
├── state/
│   └── schema.py                    # PromptOptimiserState TypedDict
├── nodes/
│   ├── run_prompt.py                # Node 1: runs prompt on all test cases (parallel)
│   ├── score_output.py              # Node 2: LLM-as-judge scoring (parallel)
│   ├── analyse_weakness.py          # Node 3: diagnoses root cause of low score
│   ├── rewrite_prompt.py            # Node 4: rewrites prompt based on weakness
│   └── convergence.py              # Node 5: checks exit conditions + routes
├── rubrics/
│   ├── cv_bullet_rubric.json        # CV bullet rewriter rubric
│   ├── cv_jd_match_rubric.json      # CV vs JD match rubric
│   └── cold_outreach_rubric.json    # Cold outreach message rubric
├── test_cases/
│   ├── cv_bullet_test_cases.json    # 8 test cases for CV bullets
│   ├── cv_jd_match_test_cases.json  # 8 test cases for CV vs JD match
│   └── cold_outreach_test_cases.json # 8 test cases for cold outreach
├── runs/                            # Auto-generated run logs (JSON, one per run)
└── dashboard.py                     # Streamlit score curve + diff visualisation
```

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd prompt-optimiser
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
OPENAI_API_KEY=sk-proj-...
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=prompt-optimiser
```

> **LangSmith** (optional but recommended): sign up free at [smith.langchain.com](https://smith.langchain.com). It gives you a visual trace of every iteration — what the agent tried, why it rewrote the prompt, and how scores evolved.

### 3. Run the agent on an existing use case

```bash
python3 main.py \
  --task "rewrite a weak CV bullet into a strong impact-first quantified bullet" \
  --rubric rubrics/cv_bullet_rubric.json \
  --test-cases test_cases/cv_bullet_test_cases.json \
  --seed-prompt "Rewrite this CV bullet to be stronger and more impactful."
```

### 4. View the dashboard

```bash
streamlit run dashboard.py
```

Opens a browser showing: score curve across iterations, best prompt found, side-by-side diff of seed vs best prompt.

---

## Ready-to-use cases

Three use cases are already set up with rubrics and test cases:

| Use case | Rubric | Test cases | Seed prompt |
|---|---|---|---|
| CV bullet rewriter | `rubrics/cv_bullet_rubric.json` | `test_cases/cv_bullet_test_cases.json` | `"Rewrite this CV bullet to be stronger and more impactful."` |
| CV vs JD match | `rubrics/cv_jd_match_rubric.json` | `test_cases/cv_jd_match_test_cases.json` | `"Compare this CV against the job description and tell me how well I match."` |
| Cold outreach message | `rubrics/cold_outreach_rubric.json` | `test_cases/cold_outreach_test_cases.json` | `"Write a cold LinkedIn message to the hiring manager for this role."` |

Run commands for each:

```bash
# CV bullet rewriter
python3 main.py \
  --task "rewrite a weak CV bullet into a strong impact-first quantified bullet" \
  --rubric rubrics/cv_bullet_rubric.json \
  --test-cases test_cases/cv_bullet_test_cases.json \
  --seed-prompt "Rewrite this CV bullet to be stronger and more impactful."

# CV vs JD match
python3 main.py \
  --task "analyse how well a CV matches a job description and give specific improvement actions" \
  --rubric rubrics/cv_jd_match_rubric.json \
  --test-cases test_cases/cv_jd_match_test_cases.json \
  --seed-prompt "Compare this CV against the job description and tell me how well I match."

# Cold outreach
python3 main.py \
  --task "write a cold LinkedIn outreach message to a hiring manager that gets a reply" \
  --rubric rubrics/cold_outreach_rubric.json \
  --test-cases test_cases/cold_outreach_test_cases.json \
  --seed-prompt "Write a cold LinkedIn message to the hiring manager for this role."
```

---

## Adding a new use case

To optimise a prompt for any new task, you need two files and one command. The agent code never changes.

### Step 1 — Write your rubric

Create `rubrics/your_task_rubric.json`. The rubric defines what "good output" looks like — dimensions, weights, and scoring guidance for the judge.

```json
{
  "task": "One sentence describing what the prompt is supposed to do",
  "scoring_calibration": "Be strict. Reserve 9-10 only for outputs that are genuinely excellent. Most outputs should score 5-7.",
  "dimensions": [
    {
      "name": "dimension_name",
      "description": "What this dimension measures. Be specific — vague descriptions produce vague scoring.",
      "weight": 0.40,
      "scoring_guide": {
        "1-3": "What a bad output looks like on this dimension",
        "4-6": "What a mediocre output looks like",
        "7-8": "What a good output looks like",
        "9-10": "What an excellent output looks like — be very specific here"
      }
    }
  ]
}
```

**Rules for a good rubric:**
- Weights must sum to 1.0
- Use 2–5 dimensions — more than 5 confuses the judge
- The `scoring_guide` for 9-10 must be strict and specific — if it's easy to score 9+, the agent converges too fast
- Add `"scoring_calibration"` to tell the judge to score hard — without it the judge is generous and the agent stops iterating too early

### Step 2 — Write your test cases

Create `test_cases/your_task_test_cases.json`. Test cases are synthetic inputs that stress-test the prompt — they are not real data.

```json
[
  {
    "id": "tc_001",
    "tags": ["ideal", "strong_input"],
    "description": "What this test case is testing",
    "input": {
      "field_one": "value one",
      "field_two": "value two"
    },
    "expected_output": "Description of what a perfect output looks like for this input"
  }
]
```

**Rules for good test cases:**
- Write 8 minimum — fewer than 6 gives the agent too narrow a view of the task
- Cover the full range: ideal input, vague input, edge case, domain-specific, minimal info
- `input` can be a plain string or a dict with named fields — both work
- `expected_output` is optional but helps the judge score more accurately
- Diversity beats quantity — 8 varied cases is better than 20 similar ones

**Checklist for 8 test cases:**

| # | Type | Why |
|---|---|---|
| 1 | Ideal input | Sets the quality ceiling |
| 2 | Vague/minimal input | Tests graceful handling of sparse info |
| 3 | Edge case | Something unusual the prompt might break on |
| 4 | Domain-specific | Tests if the prompt handles specialist context |
| 5 | Common failure mode | The most typical weak input for this task |
| 6 | Overloaded input | Too much information — tests conciseness |
| 7 | Ambiguous input | Multiple valid interpretations |
| 8 | Real-world messy input | Realistic imperfect input |

### Step 3 — Run the agent

```bash
python3 main.py \
  --task "one sentence describing what the prompt should do" \
  --rubric rubrics/your_task_rubric.json \
  --test-cases test_cases/your_task_test_cases.json \
  --seed-prompt "Your starting prompt — intentionally simple is fine."
```

### Step 4 — Read the output

When the run finishes, the terminal prints:

```
Best score : 8.9
Best prompt:
[the optimised prompt text]

Run log saved to runs/abc123_20240115_143022.json
```

Copy the best prompt. Use it in Claude.ai or ChatGPT for your daily work.

### Step 5 — Use the best prompt

Open Claude.ai. Paste the best prompt as your first message, then paste your real input. That's it.

```
[paste best prompt here]

[paste your real input here]
```

---

## Tuning the agent

If the agent converges too fast (finishes in 0-2 iterations), make these changes:

**Raise the convergence threshold** in `nodes/convergence.py`:
```python
TARGET_SCORE = 9.2   # default is 8.5 — raise to force more iterations
```

**Tighten the rubric** — make the 9-10 scoring criteria stricter so the judge scores harder. Add or sharpen the `scoring_calibration` field.

**Use a weaker seed prompt** — starting from `"Do X."` forces the agent to do more rewriting than starting from a detailed instruction.

If the agent takes too long (over 10 minutes), check:

- `score_output.py` uses `asyncio.gather` for parallel scoring — if not, add it
- Reduce to 4–5 test cases for faster iteration during development
- Switch `run_prompt` model from `gpt-4o` to `gpt-4o-mini` if inputs are simple

---

## How to read the run log

Every run saves a JSON file to `runs/`. Key fields:

```json
{
  "best_prompt": "the best prompt found",
  "best_score": 8.9,
  "score_history": [5.8, 6.4, 7.1, 8.2, 8.9],
  "weakness_log": [
    "Iteration 1: prompt does not constrain output length...",
    "Iteration 2: prompt lacks instruction to include metrics..."
  ],
  "iteration": 5
}
```

`weakness_log` shows you exactly what the agent diagnosed each round — useful for understanding what dimensions your seed prompt was missing.

---

## Frequently asked questions

**Do I use real data in test cases?**
No. Test cases are synthetic stress-test inputs written to cover edge cases. Your real inputs are never used during the optimisation run — only after you have the best prompt.

**How often do I rerun the agent?**
Once per task type — unless your requirements change (different output format, different audience, different constraints). The optimised prompt is stable until the task itself changes.

**The score isn't improving — what do I do?**
1. Check the `weakness_log` in the run JSON — if the agent keeps diagnosing the same weakness, the rewriter is stuck
2. Try a different seed prompt that addresses the stuck dimension directly
3. Tighten the rubric's 9-10 scoring criteria to give the rewriter a clearer target

**What kinds of tasks can I use this for?**
Anything where you have a repeatable prompt task: summarisation, rewriting, classification, extraction, analysis, drafting, critique, transformation. If you find yourself giving the same instruction to an LLM more than a few times, it's worth optimising.

**How long does a run take?**
Typically 5–15 minutes depending on the number of test cases, iterations needed, and model speed. Most runs converge in 4–8 iterations.

**Do I need LangSmith?**
No — it's optional. The agent runs and saves results locally without it. LangSmith adds a visual trace of every iteration, which is useful for debugging why the agent made specific rewrites.

---

## Stack

| Component | Tool |
|---|---|
| Agent orchestration | LangGraph |
| Prompt execution | gpt-4o-mini |
| Judge + rewriter | gpt-4o |
| Tracing | LangSmith |
| Dashboard | Streamlit |
| Run persistence | Local JSON (runs/ folder) |
