export type Contribution = {
  file: string;
  lines_authored: number;
  commits: number;
  first_contribution: string;
  last_contribution: string;
  ownership_pct: number;
};

export type Reviewer = {
  handle: string;
  display_name: string;
  expertise_score: number;
  seniority_score: number;
  contributions: Contribution[];
};

export type FileSummary = {
  path: string;
  additions: number;
  deletions: number;
  patch_snippet: string;
};

export type OutcomeContrast = {
  actual_lines: string[];
  proposed_lines: string[];
};

export type CostLink = {
  text: string;
  url: string;
};

export type ScoredPR = {
  repo: string;
  pr_number: number;
  title: string;
  author: string;
  url: string;
  closed_at: string;
  files_changed: FileSummary[];
  actual_reviewers: Reviewer[];
  best_pick: Reviewer | null;
  reasoning: string;
  cost_of_gap: string;
  cost_of_gap_links?: CostLink[];
  outcome_contrast?: OutcomeContrast;
  reviewer_match?: boolean;
  computed_at: string;
};
