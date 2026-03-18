from __future__ import annotations

from datetime import date


REQUIRED_TYPES = ["moed_a_start", "moed_a_end", "moed_b_start", "moed_b_end"]


def _is_valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(str(value))
        return True
    except Exception:
        return False


def validate_events(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    present = {row.get("event_type") for row in rows}

    for required in REQUIRED_TYPES:
        if required not in present:
            errors.append(f"Missing required event type: {required}")

    for idx, row in enumerate(rows, start=1):
        start_date = row.get("start_date")
        end_date = row.get("end_date")

        if not start_date or not _is_valid_iso_date(start_date):
            errors.append(f"Row {idx}: start_date is invalid")
            continue

        if end_date:
            if not _is_valid_iso_date(end_date):
                errors.append(f"Row {idx}: end_date is invalid")
                continue
            if date.fromisoformat(start_date) > date.fromisoformat(end_date):
                errors.append(f"Row {idx}: start_date cannot be after end_date")

    return errors
