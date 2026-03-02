"use server";

import path from "path";
import type { ReportDetail, ReviewFieldKey, FieldSources } from "@/lib/types";
import { REVIEW_FIELDS } from "@/lib/types";
import { runPython } from "./runPython";
import { parseBridgeError } from "./parseBridgeError";

/**
 * Fetch detailed field data for a single report from Oracle via the Python bridge.
 *
 * Falls back to demo data when the Python bridge is unavailable.
 *
 * @returns An object with the report detail and whether demo data is being used.
 */
export async function getReportDetails(
  normalizedName: string,
): Promise<{ report: ReportDetail; isDemo: boolean; demoReason?: string }> {
  try {
    const scriptPath = path.join(
      process.cwd(),
      "server",
      "oracle_bridge_detail.py",
    );
    const data = await runPython(scriptPath, [normalizedName]);
    const raw = JSON.parse(data) as {
      normalizedName: string;
      name: string;
      fields: Record<string, FieldSources>;
      review?: Record<string, string | null>;
    };

    // Ensure every expected field is present
    const fields = {} as Record<ReviewFieldKey, FieldSources>;
    for (const key of REVIEW_FIELDS) {
      fields[key] = raw.fields[key] ?? {
        ground_truth: null,
        llm: null,
        similarity: null,
      };
    }

    // Process review data if present
    const review: Record<ReviewFieldKey, string | null> | undefined = raw.review
      ? (Object.fromEntries(
          REVIEW_FIELDS.map((key) => [key, raw.review![key] ?? null])
        ) as Record<ReviewFieldKey, string | null>)
      : undefined;

    return {
      report: {
        normalizedName: raw.normalizedName,
        name: raw.name,
        fields,
        review,
      },
      isDemo: false,
    };
  } catch (err) {
    const reason = parseBridgeError(err);
    console.warn(
      "[getReportDetails] Oracle bridge unavailable, using demo data:",
      reason,
    );
    return { report: getDemoReportDetail(normalizedName), isDemo: true, demoReason: reason };
  }
}
function getDemoReportDetail(normalizedName: string): ReportDetail {
  const demoValues: Record<ReviewFieldKey, FieldSources> = {
    page_count: {
      ground_truth: "125",
      llm: "125",
      similarity: "1.00",
    },
    nsc: {
      ground_truth: "NSC-123456",
      llm: "NSC-123456",
      similarity: "1.00",
    },
    compound_name: {
      ground_truth: "Compound X-100",
      llm: "Compound X-100",
      similarity: "0.98",
    },
    species: {
      ground_truth: "Sprague-Dawley Rat",
      llm: "Sprague Dawley Rats",
      similarity: "0.91",
    },
    contractor_name: {
      ground_truth: "MedTox Laboratories",
      llm: "MedTox Labs Inc.",
      similarity: "0.85",
    },
    type_of_study: {
      ground_truth: "28-Day Repeated Dose Toxicity",
      llm: "28-day repeat dose toxicity study",
      similarity: "0.88",
    },
    dosing_period: {
      ground_truth: "28 days",
      llm: "28 days",
      similarity: "1.00",
    },
    schedule_of_administration: {
      ground_truth: "Once daily by oral gavage",
      llm: "Daily oral gavage",
      similarity: "0.82",
    },
    report_year: {
      ground_truth: "2023",
      llm: "2023",
      similarity: "1.00",
    },
    report_month: {
      ground_truth: "June",
      llm: "Jun",
      similarity: "0.90",
    },
    study_project_number: {
      ground_truth: "PRJ-2023-0456",
      llm: "PRJ-2023-0456",
      similarity: "1.00",
    },
    glp: {
      ground_truth: "Yes",
      llm: "GLP compliant",
      similarity: "0.75",
    },
    summary: {
      ground_truth:
        "A 28-day repeated dose oral toxicity study of Compound X-100 was conducted in Sprague-Dawley rats.",
      llm: "This study evaluated the toxicity of Compound X-100 administered orally to rats over 28 days.",
      similarity: "0.79",
    },
  };

  return {
    normalizedName,
    name: `${normalizedName}.txt`,
    fields: demoValues,
  };
}