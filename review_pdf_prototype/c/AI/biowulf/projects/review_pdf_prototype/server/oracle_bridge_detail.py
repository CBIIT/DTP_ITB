"""
oracle_bridge_detail.py — Fetch all source rows for a single report.
Usage:
    python oracle_bridge_detail.py <normalized_name>
Reads credentials from environment variables:
    ORACLE_USER, ORACLE_PASSWORD, ORACLE_CONNECTION_STRING
Outputs a JSON object with field values grouped by source to stdout.
"""
import json
import sys
from oracle_connection import get_connection

# The data columns to extract (must match the DB column names - uppercase).
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

def fetch_report_detail(normalized_name: str):
    """Return structured field data for a single report."""
    conn = get_connection()
    cursor = conn.cursor()
    col_list = ", ".join(FIELD_COLUMNS)
    cursor.execute(
        f"""
        SELECT NORMALIZED_NAME, NAME, SOURCE, {col_list}
        FROM report_rows_subset
        WHERE NORMALIZED_NAME = :name
        ORDER BY SOURCE
        """,
        {"name": normalized_name},
    )
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor]
    cursor.close()
    conn.close()

    if not rows:
        return {"error": f"No rows found for '{normalized_name}'"}

    # Group field values by source
    fields: dict[str, dict[str, str | None]] = {}
    # Use lowercase keys for the fields object to match frontend expectations
    field_keys = [f.lower() for f in FIELD_COLUMNS]
    for field_key in field_keys:
        fields[field_key] = {"ground_truth": None, "llm": None, "similarity": None}
    
    # Track review selections
    review_data: dict[str, str | None] = {}

    for row in rows:
        source = row.get("SOURCE", "").strip().lower()
        # Map 'ground-truth' to 'ground_truth' for consistency
        if source == "ground-truth":
            source = "ground_truth"
        
        if source == "review":
            # Store review data separately
            for i, field_col in enumerate(FIELD_COLUMNS):
                field_key = field_keys[i]
                value = row.get(field_col)
                review_data[field_key] = str(value) if value is not None else None
        elif source in ("ground_truth", "llm", "similarity"):
            for i, field_col in enumerate(FIELD_COLUMNS):
                field_key = field_keys[i]
                value = row.get(field_col)
                fields[field_key][source] = str(value) if value is not None else None

    return {
        "normalizedName": rows[0].get("NORMALIZED_NAME"),
        "name": rows[0].get("NAME"),
        "fields": fields,
        "review": review_data if review_data else None,
    }
    
def main():
    if len(sys.argv) < 2:
        print(
            json.dumps({"error": "Usage: oracle_bridge_detail.py <normalized_name>"}),
            file=sys.stderr,
        )
        sys.exit(1)
    normalized_name = sys.argv[1]
    try:
        detail = fetch_report_detail(normalized_name)
        print(json.dumps(detail))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()