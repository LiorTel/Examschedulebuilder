from __future__ import annotations

from phase_a.hebrew_utils import detect_semester_from_text
from phase_a.models import EVENT_TYPES, ExtractedRecord


def detect_event_type(text: str, section_context: str) -> str:
    normalized = text.replace('"', "").replace("'", "")

    if "היום הראשון ללימודים" in normalized or "היום הראשון לסמסטר" in normalized:
        return "semester_start"
    if "היום האחרון לסמסטר" in normalized or "היום האחרון של סמסטר" in normalized:
        return "semester_end"
    if "ימי היערכות לבחינות" in normalized:
        return "exam_prep_period"
    if "תחילת תקופת הבחינות" in normalized or "תקופת בחינות" in normalized:
        return "exam_period"
    if "יום אוריינטציה" in normalized:
        return "orientation_day"
    if "יום פתוח" in normalized:
        return "open_day"
    if "האוניברסיטה סגורה" in normalized:
        return "university_closed"
    if "אין לימודים" in normalized:
        return "no_studies_day"
    if "הפסקת לימודים" in normalized:
        return "partial_block"
    if "הלימודים יסתיימו בשעה" in normalized:
        return "reduced_hours_day"
    if "יום השלמה" in normalized:
        return "makeup_day"
    if "פסיכומטרית" in normalized or "פסיכומטרי" in normalized:
        return "psychometric_block"
    if "בחינות סמסטר ראשון בתיכון" in normalized:
        return "external_exam_block"

    if section_context == "חגים ומועדים נוספים":
        if "סגורה" in normalized:
            return "university_closed"
        if "אין לימודים" in normalized:
            return "no_studies_day"
        return "holiday"

    if "חופשת" in normalized or "פגרת" in normalized:
        return "holiday"
    if "פתיחת שנה" in normalized:
        return "informational_event"

    return "unknown"


def _default_shape(event_type: str, is_range: bool, has_time: bool) -> dict:
    defaults = {
        "semester_start": ("high", "informational", "none"),
        "semester_end": ("high", "informational", "none"),
        "exam_prep_period": ("high", "no_classes", "date_range" if is_range else "full_day"),
        "exam_period": ("high", "no_exams", "date_range"),
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


def _confidence_for(event_type: str) -> float:
    return {
        "semester_start": 0.95,
        "semester_end": 0.95,
        "exam_prep_period": 0.94,
        "exam_period": 0.93,
        "orientation_day": 0.92,
        "open_day": 0.9,
        "university_closed": 0.94,
        "no_studies_day": 0.92,
        "partial_block": 0.9,
        "reduced_hours_day": 0.9,
        "makeup_day": 0.9,
        "psychometric_block": 0.95,
        "external_exam_block": 0.95,
        "informational_event": 0.8,
        "holiday": 0.8,
        "unknown": 0.5,
    }[event_type]


def classify_candidates(candidates: list[dict]) -> list[ExtractedRecord]:
    records: list[ExtractedRecord] = []

    for candidate in candidates:
        source_text = candidate["source_text"]
        event_name = candidate.get("event_name") or source_text
        section_context = candidate.get("section_context", "GENERAL")

        event_type = detect_event_type(f"{event_name} {source_text}", section_context)

        if candidate.get("in_no_exam_section") and event_type in {"holiday", "informational_event", "unknown"}:
            event_type = "external_exam_block"

        if event_type not in EVENT_TYPES:
            event_type = "unknown"

        has_time = bool(candidate.get("start_time") or candidate.get("end_time"))
        is_open_ended = event_type == "exam_period" and not candidate.get("end_date")
        is_range = bool(candidate.get("end_date")) or is_open_ended
        requires_manual_review = bool(candidate.get("requires_manual_review", False)) or is_open_ended

        notes = candidate.get("notes")
        if is_open_ended:
            notes = "; ".join(filter(None, [notes, "missing end date"])) if notes else "missing end date"

        shape = _default_shape(event_type, bool(candidate.get("end_date")), has_time)

        semester = candidate.get("semester_context") or detect_semester_from_text(source_text) or "NONE"
        if event_type == "informational_event" and semester == "NONE" and "תשפ" in source_text:
            semester = "NEXT_YEAR"

        records.append(
            ExtractedRecord(
                event_name=event_name,
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
                source_text=source_text,
                confidence_score=_confidence_for(event_type),
            )
        )

    return records
