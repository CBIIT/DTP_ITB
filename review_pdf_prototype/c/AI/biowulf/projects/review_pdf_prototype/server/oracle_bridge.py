"""
oracle_bridge.py — Fetch the list of distinct reports from Oracle.
Usage:
    python oracle_bridge.py
Reads credentials from environment variables:
    ORACLE_USER, ORACLE_PASSWORD, ORACLE_CONNECTION_STRING
Outputs a JSON array of report objects to stdout.
"""
import json
import sys
from oracle_connection import get_connection

FIELD_COLUMNS = [
    "PAGE_COUNT",
    "NSC",
    "COMPOUND_NAME",
    "SPECIES",
    "CONTRACTOR_NAME",
    "TYPE_OF_STUDY",
    "DOSING_PERIOD",
    "SCHEDULE_OF_ADMINISTRATION",
    "REPORT_YEAR",
    "REPORT_MONTH",
    "STUDY_OR_PROJECT_NUMBER",
    "GLP",
    "SUMMARY",
]

def fetch_reports():
    """Query distinct reports and their review status from the subset table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all unique reports
    cursor.execute(
        """
        SELECT DISTINCT NORMALIZED_NAME, NAME
        FROM report_rows_subset
        WHERE SOURCE = 'ground-truth'
        ORDER BY NORMALIZED_NAME
        """
    )
    # Fetch all rows before reusing the connection for inner queries
    all_reports = cursor.fetchall()
    
    # Build the review-field count expression once
    col_checks = " + ".join(
        f"CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END"
        for col in FIELD_COLUMNS
    )
    
    reports = []
    review_cursor = conn.cursor()
    for row in all_reports:
        normalized_name = row[0]
        name = row[1]
        
        # Check if a review exists and count filled fields
        review_cursor.execute(
            f"""
            SELECT {col_checks} as fields_reviewed
            FROM report_rows_subset
            WHERE NORMALIZED_NAME = :name AND SOURCE = 'review'
            """,
            {"name": normalized_name}
        )
        
        review_row = review_cursor.fetchone()
        fields_reviewed = review_row[0] if review_row else 0
        
        reports.append(
            {
                "normalizedName": normalized_name,
                "name": name,
                "fieldsReviewed": fields_reviewed,
            }
        )
    
    review_cursor.close()
    cursor.close()
    conn.close()
    return reports

def main():
    try:
        reports = fetch_reports()
        print(json.dumps(reports))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()