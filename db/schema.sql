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

CREATE INDEX idx_runs_run_id ON runs (run_id);
CREATE INDEX idx_runs_created_at ON runs (created_at DESC);
