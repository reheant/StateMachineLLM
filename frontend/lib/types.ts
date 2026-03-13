export interface Run {
  strategy: "single_prompt" | "two_shot_prompt";
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
}

export interface Example {
  key: string;
  icon: string;
  label: string;
  blurb: string;
}
