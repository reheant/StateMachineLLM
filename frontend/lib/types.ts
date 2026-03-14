export interface Run {
  strategy:
    | "single_prompt"
    | "two_shot_prompt"
    | "mermaid_compiler"
    | "automatic_grader";
  date: string;
  time: string;
  model: string;
  system: string;
  folder: string;
  has_png: boolean;
}

export interface Artifacts {
  png: string | null;
  mmd: string | null;
  txt: string | null;
  llm_log: string | null;
  grading_prompt: string | null;
  grading_output: string | null;
  ground_truth_csv: string | null;
  grading_csv: string | null;
  grading_tsv: string | null;
}

export interface Example {
  key: string;
  icon: string;
  label: string;
  blurb: string;
  description?: string;
}
