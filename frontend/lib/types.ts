export interface Run {
  strategy:
    | "single_prompt"
    | "two_stage_prompt"
    | "mermaid_compiler"
    | "automatic_grader";
  date: string;
  time: string;
  model: string;
  system: string;
  folder: string;
  has_png: boolean;
  run_status?: "in_progress" | "success" | "partial" | "failed" | null;
}

export interface RunError {
  type: string;
  message: string;
  details: Record<string, unknown>;
  attempts: number;
}

export interface RunStatus {
  status: "in_progress" | "success" | "partial" | "failed";
  error: RunError | null;
  completed_at: string | null;
}

export interface Artifacts {
  png: string | null;
  mmd: string | null;
  txt: string | null;
  stage1_png?: string | null;
  stage1_mmd?: string | null;
  stage1_txt?: string | null;
  llm_log: string | null;
  grading_prompt: string | null;
  grading_output: string | null;
  ground_truth_csv: string | null;
  grading_csv: string | null;
  grading_tsv: string | null;
  status: RunStatus | null;
}

export interface Example {
  key: string;
  icon: string;
  label: string;
  blurb: string;
  description?: string;
}
