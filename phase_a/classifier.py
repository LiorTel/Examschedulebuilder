from __future__ import annotations

import re

from phase_a.hebrew_utils import detect_semester_from_text
from phase_a.models import EVENT_TYPES, ExtractedRecord


def _default_shape(event_type: str, is_range: bool, has_time: bool) -> dict:
    defaults = {
        "semester_start": ("high", "informational", "none"),
        "semester_end": ("high", "informational", "none"),
        "exam_prep_period": ("high", "no_classes", "date_range" if is_range else "full_day"),
        "exam_period": ("high", "no_exams", "date_range" if is_range else "date_range"),
        "orientation_day": ("medium", "informational", "none"),
        "open_day": ("low", "informational", "none"),
        "university_closed": ("high", "no_exams", "date_range" if is_range else "full_day"),
        "no_studies_day": ("high", "no_classes", "date_range" if is_range else "full_day"),
        "partial_block": ("high", "no_exam_after_time", "partial_day"),
        "reduced_hours_day": ("medium", "reduced_hours", "partial_day"),
        "makeup_day": ("medium", "informational", "none"),
        "psychometric_block": ("high", "no_exams", "date_range" if is_range else "full_day"),
        "external_exam_block": ("high", "no_exams", "partial_day" if has_time else "full_day"),
        "informational_event": ("low", "informational", "none"),
        "holiday": ("medium", "informational", "date_range" if is_range else "full_day"),
        "unknown": ("medium", "informational", "none"),
    }
    relevance, constraint, scope = defaults[event_type]
    return {"scheduling_relevance": relevance, "constraint_type": constraint, "block_scope": scope}


def classify_candidate(candidate: dict) -> tuple[str, dict, float, bool, bool, str | None]:
    source_text = candidate["source_text"]
    name = candidate.get("event_name", "")
    text = f"{name} {source_text}"

    event_type = "unknown"
    confidence = 0.52

    if "היום הראשון" in text and ("לימודים" in text or "סמסטר" in text):
        event_type, confidence = "semester_start", 0.95
    elif "היום האחרון לסמסטר" in text or "היום האחרון של סמסטר" in text:
        event_type, confidence = "semester_end", 0.95
    elif "ימי היערכות לבחינות" in text:
        event_type, confidence = "exam_prep_period", 0.94
    elif "תקופת בחינות" in text or "תחילת תקופת הבחינות" in text:
        event_type, confidence = "exam_period", 0.93
    elif "יום אוריינטציה" in text:
        event_type, confidence = "orientation_day", 0.92
    elif "יום פתוח" in text:
        event_type, confidence = "open_day", 0.9
    elif "האוניברסיטה סגורה" in text:
        event_type, confidence = "university_closed", 0.94
    elif "אין לימודים" in text:
        event_type, confidence = "no_studies_day", 0.92
    elif "הפסקת לימודים" in text:
        event_type, confidence = "partial_block", 0.9
    elif "הלימודים יסתיימו בשעה" in text:
        event_type, confidence = "reduced_hours_day", 0.9
    elif "יום השלמה" in text:
        event_type, confidence = "makeup_day", 0.9
    elif "פסיכומטרית" in text or "פסיכומטרי" in text:
        event_type, confidence = "psychometric_block", 0.95
    elif 'בחינות "סמסטר ראשון בתיכון"' in text:
        event_type, confidence = "external_exam_block", 0.95
    elif "חופשת" in text or "פגרת" in text:
        event_type, confidence = "holiday", 0.8
    elif "פתיחת שנה" in text:
        event_type, confidence = "informational_event", 0.8

    if candidate.get("in_no_exam_section") and event_type in {"holiday", "informational_event", "unknown"}:
        event_type = "external_exam_block"
        confidence = max(confidence, 0.75)

    if candidate.get("section_context") == "חגים ומועדים נוספים" and event_type in {"unknown", "informational_event"}:
        event_type = "holiday"
        confidence = max(confidence, 0.7)

    has_time = bool(candidate.get("start_time") or candidate.get("end_time"))
    is_open_ended = False
    requires_manual_review = bool(candidate.get("requires_manual_review", False))
    notes = candidate.get("notes")

    if event_type == "exam_period" and not candidate.get("end_date"):
        is_open_ended = True
        requires_manual_review = True
        notes = "; ".join(filter(None, [notes, "missing end date"])) if notes else "missing end date"

    if event_type == "unknown" and ("אין לימודים" in text or "סגורה" in text or "בחינות" in text):
        requires_manual_review = True

    shape = _default_shape(event_type, bool(candidate.get("end_date")), has_time)
    if has_time and event_type == "external_exam_block":
        shape["block_scope"] = "partial_day"
    if has_time and event_type in {"partial_block", "reduced_hours_day"} and candidate.get("start_time") and not candidate.get("end_time"):
        shape["constraint_type"] = "no_exam_after_time"

    if event_type not in EVENT_TYPES:
        event_type = "unknown"

    return event_type, shape, confidence, is_open_ended, requires_manual_review, notes


def classify_candidates(candidates: list[dict]) -> list[ExtractedRecord]:
    records: list[ExtractedRecord] = []
    for candidate in candidates:
        event_type, shape, confidence, is_open_ended, requires_manual_review, notes = classify_candidate(candidate)
        semester = candidate.get("semester_context") or detect_semester_from_text(candidate["source_text"]) or "NONE"

        if event_type == "informational_event" and semester == "NONE" and "תשפ" in candidate["source_text"]:
            semester = "NEXT_YEAR"

        is_range = bool(candidate.get("end_date")) or is_open_ended

        records.append(
            ExtractedRecord(
                event_name=candidate.get("event_name") or candidate["source_text"],
                event_type=event_type,
                semester=semester,
                start_date=candidate["start_date"],
                end_date=candidate.get("end_date"),
                is_range=is_range,
                is_open_ended=is_open_ended,
                constraint_type=shape["constraint_type"],
                scheduling_relevance=shape["scheduling_relevance"],
                block_scope=shape["block_scope"],
                start_time=candidate.get("start_time"),
                end_time=candidate.get("end_time"),
                requires_manual_review=requires_manual_review,
                notes=notes,
                source_text=candidate["source_text"],
                confidence_score=confidence,
            )
        )
    return records
