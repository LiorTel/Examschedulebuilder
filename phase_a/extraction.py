from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional


DATE_TOKEN = r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b"
RANGE_PATTERN = re.compile(rf"({DATE_TOKEN})\s*(?:-|–|to|עד)\s*({DATE_TOKEN})", re.IGNORECASE)
SINGLE_PATTERN = re.compile(DATE_TOKEN)


def infer_year_from_academic_year(academic_year: str, month: int) -> int:
    """Infer Gregorian year by month from an academic year like 2025-2026."""
    years = re.findall(r"\d{4}", academic_year)
    if len(years) >= 2:
        start_year, end_year = int(years[0]), int(years[1])
        return start_year if month >= 8 else end_year
    if len(years) == 1:
        return int(years[0])
    return date.today().year


def normalize_date(value: str, academic_year: str) -> Optional[date]:
    value = value.strip()
    for sep in ["/", ".", "-"]:
        if sep in value:
            parts = value.split(sep)
            break
    else:
        return None

    if len(parts) not in (2, 3):
        return None

    try:
        day = int(parts[0])
        month = int(parts[1])
        if len(parts) == 3:
            year = int(parts[2])
            if year < 100:
                year += 2000
        else:
            year = infer_year_from_academic_year(academic_year, month)
        return date(year, month, day)
    except ValueError:
        return None


def extract_date_candidates(text: str, academic_year: str) -> list[dict]:
    candidates: list[dict] = []
    for line in [ln.strip() for ln in text.splitlines() if ln.strip()]:
        range_match = RANGE_PATTERN.search(line)
        if range_match:
            start_raw, end_raw = range_match.group(1), range_match.group(2)
            start_date = normalize_date(start_raw, academic_year)
            end_date = normalize_date(end_raw, academic_year)
            if start_date:
                candidates.append(
                    {
                        "source_text": line,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )
            continue

        for single in SINGLE_PATTERN.finditer(line):
            start_date = normalize_date(single.group(0), academic_year)
            if start_date:
                candidates.append(
                    {
                        "source_text": line,
                        "start_date": start_date,
                        "end_date": None,
                    }
                )
    return candidates
