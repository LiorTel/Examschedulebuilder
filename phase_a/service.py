from __future__ import annotations

from phase_a.classifier import classify_candidates
from phase_a.extraction import extract_date_candidates
from phase_a.parsers import parse_uploaded_file


def process_calendar_file(file_name: str, file_bytes: bytes, academic_year: str) -> list[dict]:
    parsed = parse_uploaded_file(file_name, file_bytes)
    combined_text = "\n".join([parsed.raw_text, *parsed.table_rows])
    candidates = extract_date_candidates(combined_text, academic_year)
    records = classify_candidates(candidates)
    return [record.to_row() for record in records]
