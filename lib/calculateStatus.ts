import type { ReportStatus, ReportSelections } from "./types";
import { REVIEW_FIELDS } from "./types";

/**
 * Calculate review status for a report based on its selections.
 *
 * @returns An object with the status label, number of fields reviewed, and total fields.
 */
export function calculateStatus(selections: ReportSelections): {
  status: ReportStatus;
  fieldsReviewed: number;
  totalFields: number;
} {
  const totalFields = REVIEW_FIELDS.length;
  const fieldsReviewed = REVIEW_FIELDS.filter(
    (key) => selections[key] !== undefined,
  ).length;

  let status: ReportStatus;
  if (fieldsReviewed === 0) {
    status = "not-started";
  } else if (fieldsReviewed === totalFields) {
    status = "done";
  } else {
    status = "in-progress";
  }

  return { status, fieldsReviewed, totalFields };
}
