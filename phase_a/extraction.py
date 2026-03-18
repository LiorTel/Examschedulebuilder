from __future__ import annotations

import re
from datetime import date
from typing import Optional

from phase_a.hebrew_utils import HEBREW_MONTHS, normalize_hebrew_text


NUMERIC_DATE = r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?"
HEBREW_MONTHS_REGEX = "|".join(sorted(HEBREW_MONTHS.keys(), key=len, reverse=True))

RANGE_HEBREW_PATTERN = re.compile(rf"מ-?\s*({NUMERIC_DATE})\s*עד\s*({NUMERIC_DATE})")
RANGE_FULL_PATTERN = re.compile(rf"({NUMERIC_DATE})\s*[-–]\s*({NUMERIC_DATE})")
RANGE_SHORT_PATTERN = re.compile(r"(\d{1,2})\s*[-–]\s*(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})")
RANGE_MONTH_NAME_PATTERN = re.compile(rf"(\d{{1,2}})\s*[-–]\s*(\d{{1,2}})\s+ב?({HEBREW_MONTHS_REGEX})\s+(\d{{4}})")
SINGLE_MONTH_NAME_PATTERN = re.compile(rf"(\d{{1,2}})\s+ב?({HEBREW_MONTHS_REGEX})\s+(\d{{4}})")
SINGLE_NUMERIC_PATTERN = re.compile(NUMERIC_DATE)
TIME_RANGE_PATTERN = re.compile(r"מ-?\s*(\d{1,2}:\d{2})\s*עד\s*(\d{1,2}:\d{2})")
TIME_AFTER_PATTERN = re.compile(r"(?:משעה|החל משעה)\s*(\d{1,2}:\d{2})")
TIME_END_PATTERN = re.compile(r"(?:יסתיימו בשעה|עד השעה)\s*(\d{1,2}:\d{2})")


def infer_year_from_academic_year(academic_year: str, month: int) -> int:
    years = re.findall(r"\d{4}", academic_year)
    if len(years) >= 2:
        start_year, end_year = int(years[0]), int(years[1])
        return start_year if month >= 8 else end_year
    if len(years) == 1:
        return int(years[0])
    return date.today().year


def normalize_date(value: str, academic_year: str) -> Optional[date]:
    clean = value.strip()
    for sep in ["/", ".", "-"]:
        if sep in clean:
            parts = clean.split(sep)
            if len(parts) in (2, 3):
                break
    else:
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


def _parse_hebrew_month_date(day: str, month_name: str, year: str) -> Optional[date]:
    month = HEBREW_MONTHS.get(month_name)
    if not month:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def extract_times(source_text: str) -> tuple[Optional[str], Optional[str]]:
    text = normalize_hebrew_text(source_text)
    range_match = TIME_RANGE_PATTERN.search(text)
    if range_match:
        return range_match.group(1), range_match.group(2)

    start_match = TIME_AFTER_PATTERN.search(text)
    end_match = TIME_END_PATTERN.search(text)
    return (start_match.group(1) if start_match else None, end_match.group(1) if end_match else None)


def _has_machine_date_info(line: str) -> bool:
    return bool(
        re.search(NUMERIC_DATE, line)
        or re.search(rf"\d{{1,2}}\s+ב?({HEBREW_MONTHS_REGEX})\s+\d{{4}}", line)
        or re.search(rf"\d{{1,2}}\s*[-–]\s*\d{{1,2}}\s+ב?({HEBREW_MONTHS_REGEX})\s+\d{{4}}", line)
    )


def _append_candidate(
    candidates: list[dict],
    block: dict,
    start: date,
    end: Optional[date],
) -> None:
    source_text = block.get("text", "")
    start_time, end_time = extract_times(source_text)
    raw_lines = [ln.strip() for ln in block.get("lines", []) if ln.strip()]
    note_lines = [normalize_hebrew_text(ln) for ln in raw_lines[1:] if not _has_machine_date_info(ln)]

    candidates.append(
        {
            "event_name": block.get("title") or raw_lines[0] if raw_lines else source_text,
            "source_text": source_text,
            "start_date": start,
            "end_date": end,
            "is_range": bool(end),
            "semester_context": block.get("semester_context"),
            "in_no_exam_section": bool(block.get("in_no_exam_section")),
            "start_time": start_time,
            "end_time": end_time,
            "notes": "; ".join(note_lines) if note_lines else None,
        }
    )


def extract_date_candidates(blocks: list[dict], academic_year: str) -> list[dict]:
    candidates: list[dict] = []

    for block in blocks:
        source_text = block.get("text", "")
        text = normalize_hebrew_text(source_text)
        if not text:
            continue

        consumed: list[tuple[int, int]] = []

        for pattern in [RANGE_HEBREW_PATTERN, RANGE_FULL_PATTERN]:
            for match in pattern.finditer(text):
                start = normalize_date(match.group(1), academic_year)
                end = normalize_date(match.group(2), academic_year)
                if start:
                    _append_candidate(candidates, block, start, end)
                    consumed.append(match.span())

        for match in RANGE_SHORT_PATTERN.finditer(text):
            day1, day2, month, year = match.groups()
            year_value = int(year) + 2000 if len(year) == 2 else int(year)
            try:
                start = date(year_value, int(month), int(day1))
                end = date(year_value, int(month), int(day2))
            except ValueError:
                continue
            _append_candidate(candidates, block, start, end)
            consumed.append(match.span())

        for match in RANGE_MONTH_NAME_PATTERN.finditer(text):
            start = _parse_hebrew_month_date(match.group(1), match.group(3), match.group(4))
            end = _parse_hebrew_month_date(match.group(2), match.group(3), match.group(4))
            if start:
                _append_candidate(candidates, block, start, end)
                consumed.append(match.span())

        for match in SINGLE_MONTH_NAME_PATTERN.finditer(text):
            if any(a <= match.start() <= b for a, b in consumed):
                continue
            parsed = _parse_hebrew_month_date(match.group(1), match.group(2), match.group(3))
            if parsed:
                _append_candidate(candidates, block, parsed, None)
                consumed.append(match.span())

        for match in SINGLE_NUMERIC_PATTERN.finditer(text):
            if any(a <= match.start() <= b for a, b in consumed):
                continue
            parsed = normalize_date(match.group(0), academic_year)
            if parsed:
                _append_candidate(candidates, block, parsed, None)

    return candidates
