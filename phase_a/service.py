from __future__ import annotations

from phase_a.classifier import classify_candidates
from phase_a.extraction import extract_date_candidates
from phase_a.parsers import parse_uploaded_file


def process_calendar_file(file_name: str, file_bytes: bytes, academic_year: str) -> dict:
    parsed = parse_uploaded_file(file_name, file_bytes)
    candidates = extract_date_candidates(parsed.blocks, academic_year)
    records = classify_candidates(candidates)
    rows = [record.to_row() for record in records]
    return {
        "rows": rows,
        "raw_blocks": parsed.blocks,
        "candidates": candidates,
        "classified": rows,
    }
