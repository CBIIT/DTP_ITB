"""
oracle_bridge_save.py — Upsert a review row into Oracle.
Usage:
    python oracle_bridge_save.py '<json_payload>'
The JSON payload must contain:
    normalizedName  — the Normalized_Name of the report
    name            — the Name of the report
    fields          — an object mapping field keys to their resolved values
If a review row already exists for the given report, it is updated;
otherwise a new row is inserted.
Reads credentials from environment variables:
    ORACLE_USER, ORACLE_PASSWORD, ORACLE_CONNECTION_STRING
Outputs a JSON result to stdout.
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

def save_review(payload: dict):
    """Upsert a review row into report_rows_subset with Source='review'.

    If a review row already exists for this report, it is updated in place;
    otherwise a new row is inserted.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    normalized_name = payload["normalizedName"]
    name = payload["name"]
    fields = payload["fields"]
    
    # Map lowercase field keys from frontend to uppercase DB columns
    field_key_map = {
        "page_count": "PAGE_COUNT",
        "nsc": "NSC",
        "compound_name": "COMPOUND_NAME",
        "species": "SPECIES",
        "contractor_name": "CONTRACTOR_NAME",
        "type_of_study": "TYPE_OF_STUDY",
        "dosing_period": "DOSING_PERIOD",
        "schedule_of_administration": "SCHEDULE_OF_ADMINISTRATION",
        "report_year": "REPORT_YEAR",
        "report_month": "REPORT_MONTH",
        "study_project_number": "STUDY_OR_PROJECT_NUMBER",
        "glp": "GLP",
        "summary": "SUMMARY",
    }
    
    bind_values = {
        "normalized_name": normalized_name,
        "name": name,
        "source": "review",
    }
    for field_key, db_column in field_key_map.items():
        bind_values[db_column] = fields.get(field_key)
    
    # Build the SET clause for UPDATE and column/value lists for INSERT
    db_columns = list(field_key_map.values())
    update_set = ", ".join(f"t.{col} = :{col}" for col in db_columns)
    update_set += ", t.NAME = :name"
    
    all_cols = ["NORMALIZED_NAME", "NAME", "SOURCE"] + db_columns
    insert_cols = ", ".join(all_cols)
    insert_vals = ", ".join(
        ":normalized_name" if c == "NORMALIZED_NAME"
        else ":name" if c == "NAME"
        else ":source" if c == "SOURCE"
        else f":{c}"
        for c in all_cols
    )
    
    sql = f"""
        MERGE INTO report_rows_subset t
        USING (SELECT :normalized_name AS nname, :source AS src FROM dual) s
        ON (t.NORMALIZED_NAME = s.nname AND t.SOURCE = s.src)
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols})
            VALUES ({insert_vals})
    """
    
    cursor.execute(sql, bind_values)
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "normalizedName": normalized_name}

def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {"error": "Usage: oracle_bridge_save.py <json_payload>"}
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    
    payload = json.loads(sys.argv[1])
    try:
        result = save_review(payload)
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({"error": "Failed to save review: " + str(exc)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()