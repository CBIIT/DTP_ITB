/** A single row from the report_rows_subset table. */
export interface ReportRow {
  Normalized_Name: string;
  Name: string;
  Source: "ground_truth" | "llm" | "similarity";
  page_count: string | null;
  nsc: string | null;
  compound_name: string | null;
  species: string | null;
  contractor_name: string | null;
  type_of_study: string | null;
  dosing_period: string | null;
  schedule_of_administration: string | null;
  report_year: string | null;
  report_month: string | null;
  study_project_number: string | null;
  glp: string | null;
  summary: string | null;
}

/** The set of field keys that are reviewed per report. */
export const REVIEW_FIELDS = [
  "page_count",
  "nsc",
  "compound_name",
  "species",
  "contractor_name",
  "type_of_study",
  "dosing_period",
  "schedule_of_administration",
  "report_year",
  "report_month",
  "study_project_number",
  "glp",
  "summary",
] as const;

export type ReviewFieldKey = (typeof REVIEW_FIELDS)[number];

/** Human-readable labels for each review field. */
export const FIELD_LABELS: Record<ReviewFieldKey, string> = {
  page_count: "Page Count",
  nsc: "NSC",
  compound_name: "Compound Name",
  species: "Species",
  contractor_name: "Contractor Name",
  type_of_study: "Type of Study",
  dosing_period: "Dosing Period",
  schedule_of_administration: "Schedule of Administration",
  report_year: "Report Year",
  report_month: "Report Month",
  study_project_number: "Study or Project Number",
  glp: "GLP",
  summary: "Summary",
};

export type ReportStatus = "not-started" | "in-progress" | "done";

/** Summary object for a report shown on the dashboard. */
export interface ReportSummary {
  normalizedName: string;
  name: string;
  status: ReportStatus;
  fieldsReviewed: number;
  totalFields: number;
}

/** Per-field values keyed by source, used on the detail page. */
export interface FieldSources {
  ground_truth: string | null;
  llm: string | null;
  similarity: string | null;
}

/** Full detail payload for a single report. */
export interface ReportDetail {
  normalizedName: string;
  name: string;
  fields: Record<ReviewFieldKey, FieldSources>;
  review?: Record<ReviewFieldKey, string | null>;
}

/** A user's selection for one field. */
export interface FieldSelection {
  source: "ground_truth" | "llm" | "custom";
  customValue?: string;
}

/** All selections for a report, keyed by field name. */
export type ReportSelections = Partial<Record<ReviewFieldKey, FieldSelection>>;