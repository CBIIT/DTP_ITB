import csv
import json
import re
import unicodedata
from difflib import get_close_matches
from pathlib import Path


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")
    normalized = normalized.replace("_", " ")
    normalized = normalized.strip().strip('"').strip("'")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


def normalize_loose(value: str) -> str:
    basic = normalize_text(value)
    return re.sub(r"[^a-z0-9]", "", basic)


def load_metadata(csv_path: Path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    return rows


def build_indexes(metadata_rows):
    basic_index = {}
    loose_index = {}

    for row in metadata_rows:
        name = (row.get("Name") or "").strip()
        if not name:
            continue

        basic = normalize_text(name)
        loose = normalize_loose(name)

        basic_index.setdefault(basic, []).append(row)
        loose_index.setdefault(loose, []).append(row)

    return basic_index, loose_index


def select_best_candidate(candidates, target_name):
    if len(candidates) == 1:
        return candidates[0]

    target_basic = normalize_text(target_name)
    target_loose = normalize_loose(target_name)

    for candidate in candidates:
        candidate_name = candidate.get("Name", "")
        if normalize_text(candidate_name) == target_basic:
            return candidate

    for candidate in candidates:
        candidate_name = candidate.get("Name", "")
        if normalize_loose(candidate_name) == target_loose:
            return candidate

    return candidates[0]


def find_metadata_row(file_name, basic_index, loose_index):
    target_basic = normalize_text(file_name)
    target_loose = normalize_loose(file_name)

    basic_candidates = basic_index.get(target_basic)
    if basic_candidates:
        return select_best_candidate(basic_candidates, file_name), "exact_basic"

    loose_candidates = loose_index.get(target_loose)
    if loose_candidates:
        return select_best_candidate(loose_candidates, file_name), "exact_loose"

    for key, candidates in loose_index.items():
        if target_loose and (target_loose in key or key in target_loose):
            return select_best_candidate(candidates, file_name), "contains_loose"

    close = get_close_matches(target_loose, loose_index.keys(), n=1, cutoff=0.88)
    if close:
        return select_best_candidate(loose_index[close[0]], file_name), "fuzzy_loose"

    return None, "no_match"


def main():
    base_dir = Path(__file__).resolve().parent
    json_path = base_dir / "schedule_admin_training.json"
    csv_path = base_dir / "clean_metadata.csv"
    output_path = base_dir / "schedule_admin_training_sft.json"

    metadata_rows = load_metadata(csv_path)
    basic_index, loose_index = build_indexes(metadata_rows)

    with json_path.open("r", encoding="utf-8") as file:
        training_rows = json.load(file)

    merged_rows = []
    matched_count = 0
    dropped_missing_schedule_count = 0

    for row in training_rows:
        file_name = row.get("file", "")
        metadata_row, _ = find_metadata_row(file_name, basic_index, loose_index)

        schedule_value = ""
        if metadata_row:
            schedule_value = metadata_row.get("Schedule of Administration", "") or ""
            matched_count += 1

        if not str(schedule_value).strip():
            dropped_missing_schedule_count += 1
            continue

        merged_row = {
            **row,
            "Schedule of Administration": schedule_value,
        }
        merged_rows.append(merged_row)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(merged_rows, file, ensure_ascii=False, indent=2)

    print(f"Input JSON rows: {len(training_rows)}")
    print(f"Matched rows: {matched_count}")
    print(f"Unmatched rows: {len(training_rows) - matched_count}")
    print(f"Dropped (missing Schedule of Administration): {dropped_missing_schedule_count}")
    print(f"Output rows kept: {len(merged_rows)}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
