from __future__ import annotations

import re
from datetime import date


TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _is_valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(str(value))
        return True
    except Exception:
        return False


def _has_semester_boundary(rows: list[dict], semester: str, boundary: str) -> bool:
    return any(r.get("event_type") == boundary and r.get("semester") == semester for r in rows)


def validate_events(rows: list[dict]) -> list[str]:
    errors: list[str] = []

    for semester in ["A", "B"]:
        if not _has_semester_boundary(rows, semester, "semester_start"):
            errors.append(f"Missing semester {semester} start")
        if not _has_semester_boundary(rows, semester, "semester_end"):
            errors.append(f"Missing semester {semester} end")

    exam_a = [r for r in rows if r.get("event_type") == "exam_period" and r.get("semester") == "A"]
    if exam_a and any(not r.get("end_date") for r in exam_a):
        errors.append("Exam period A should be a closed range")

    for idx, row in enumerate(rows, start=1):
        start_date = row.get("start_date")
        end_date = row.get("end_date")
        event_type = row.get("event_type")

        if not start_date or not _is_valid_iso_date(start_date):
            errors.append(f"Row {idx}: start_date is invalid")
            continue

        if end_date:
            if not _is_valid_iso_date(end_date):
                errors.append(f"Row {idx}: end_date is invalid")
                continue
            if date.fromisoformat(start_date) > date.fromisoformat(end_date):
                errors.append(f"Row {idx}: end_date must be >= start_date")

        if event_type == "exam_period" and row.get("semester") == "B" and not row.get("end_date"):
            if not row.get("requires_manual_review"):
                errors.append(f"Row {idx}: open-ended exam period B must set requires_manual_review=true")

        if row.get("scheduling_relevance") == "high" and event_type == "unknown" and not row.get("requires_manual_review"):
            errors.append(f"Row {idx}: high-relevance unknown must be flagged for manual review")

        if row.get("block_scope") == "partial_day" or event_type in {"partial_block", "reduced_hours_day", "external_exam_block"}:
            for key in ["start_time", "end_time"]:
                value = row.get(key)
                if value and not TIME_PATTERN.match(str(value)):
                    errors.append(f"Row {idx}: {key} must be HH:MM")

    return errors
