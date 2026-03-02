"use server";

import path from "path";
import type { ReportDetail, ReportSelections } from "@/lib/types";
import { REVIEW_FIELDS } from "@/lib/types";
import { runPython } from "./runPython";
import { parseBridgeError } from "./parseBridgeError";

/**
 * Resolve the final value for each field based on the user's selections.
 */
function resolveFields(
  report: ReportDetail,
  selections: ReportSelections,
): Record<string, string | null> {
  const resolved: Record<string, string | null> = {};

  for (const field of REVIEW_FIELDS) {
    const sel = selections[field];
    if (!sel) {
      resolved[field] = null;
      continue;
    }
    if (sel.source === "custom") {
      resolved[field] = sel.customValue ?? null;
    } else {
      resolved[field] = report.fields[field][sel.source] ?? null;
    }
  }

  return resolved;
}

/**
 * Save review selections to Oracle (upsert: update existing or insert new row with Source='review').
 *
 * Falls back gracefully when the Python bridge is unavailable.
 *
 * @returns An object indicating success or failure.
 */
export async function saveReview(
  report: ReportDetail,
  selections: ReportSelections,
): Promise<{ success: boolean; error?: string }> {
  const resolvedFields = resolveFields(report, selections);

  const payload = {
    normalizedName: report.normalizedName,
    name: report.name,
    fields: resolvedFields,
  };

  try {
    const scriptPath = path.join(
      process.cwd(),
      "server",
      "oracle_bridge_save.py",
    );
    const data = await runPython(scriptPath, [JSON.stringify(payload)]);
    const result = JSON.parse(data);

    if (result.success) {
      return { success: true };
    }
    return { success: false, error: result.error ?? "Unknown error" };
  } catch (err) {
    const reason = parseBridgeError(err);
    console.warn("[saveReview] Oracle bridge unavailable:", reason);
    return {
      success: false,
      error: `Could not save to Oracle database: ${reason}`,
    };
  }
}
