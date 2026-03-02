"use server";

import path from "path";
import type { ReportSummary } from "@/lib/types";
import { REVIEW_FIELDS } from "@/lib/types";
import { runPython } from "./runPython";
import { parseBridgeError } from "./parseBridgeError";

/**
 * Fetch the list of reports from the Oracle database via the Python bridge.
 *
 * Falls back to demo data when the Python bridge is unavailable (e.g. no
 * Oracle connection configured).
 *
 * @returns An object with the reports array and whether demo data is being used.
 */
export async function loadReports(): Promise<{
  reports: ReportSummary[];
  isDemo: boolean;
  demoReason?: string;
}> {
  try {
    const scriptPath = path.join(
      process.cwd(),
      "server",
      "oracle_bridge.py",
    );
    const data = await runPython(scriptPath);
    const raw: { 
      normalizedName: string; 
      name: string;
      fieldsReviewed: number;
    }[] = JSON.parse(data);
    
    const totalFields = REVIEW_FIELDS.length;
    
    return {
      reports: raw.map((r) => {
        const fieldsReviewed = r.fieldsReviewed || 0;
        let status: "not-started" | "in-progress" | "done" = "not-started";
        if (fieldsReviewed === totalFields) {
          status = "done";
        } else if (fieldsReviewed > 0) {
          status = "in-progress";
        }
        
        return {
          normalizedName: r.normalizedName,
          name: r.name,
          status,
          fieldsReviewed,
          totalFields,
        };
      }),
      isDemo: false,
    };
  } catch (err) {
    const reason = parseBridgeError(err);
    console.warn(
      "[loadReports] Oracle bridge unavailable, using demo data:",
      reason,
    );
    return { reports: getDemoReports(), isDemo: true, demoReason: reason };
  }
}
function getDemoReports(): ReportSummary[] {
  const names = [
    "Study ABC-001 Acute Oral Toxicity in Rats",
    "Study ABC-002 28-Day Repeated Dose in Dogs",
    "Study ABC-003 Carcinogenicity Study in Mice",
    "Study DEF-004 Reproductive Toxicology in Rabbits",
    "Study DEF-005 Genotoxicity Assessment",
    "Study GHI-006 Chronic Toxicity in Rats",
    "Study GHI-007 Developmental Toxicity in Rats",
    "Study JKL-008 Immunotoxicity Evaluation",
    "Study JKL-009 Neurotoxicity Screening",
    "Study MNO-010 Dose Range Finding Study",
  ];

  return names.map((name) => ({
    normalizedName: name,
    name: `${name}.txt`,
    status: "not-started" as const,
    fieldsReviewed: 0,
    totalFields: REVIEW_FIELDS.length,
  }));
}
