from __future__ import annotations

from phase_a.hebrew_utils import detect_semester_from_text
from phase_a.models import EVENT_TYPES, ExtractedRecord


def _default_shape(event_type: str, is_range: bool) -> dict:
    defaults = {
        "semester_start": ("high", "informational", "none"),
        "semester_end": ("high", "informational", "none"),
        "exam_prep_period": ("high", "no_classes", "date_range" if is_range else "full_day"),
        "exam_period": ("high", "no_exams", "date_range" if is_range else "full_day"),
        "holiday": ("medium", "informational", "date_range" if is_range else "full_day"),
        "university_closed": ("high", "no_exams", "date_range" if is_range else "full_day"),
        "no_studies_day": ("high", "no_classes", "date_range" if is_range else "full_day"),
        "partial_block": ("high", "no_exam_after_time", "partial_day"),
        "reduced_hours_day": ("medium", "reduced_hours", "partial_day"),
        "open_day": ("low", "informational", "none"),
        "orientation_day": ("low", "informational", "none"),
        "makeup_day": ("medium", "informational", "none"),
        "psychometric_block": ("high", "no_exams", "date_range" if is_range else "full_day"),
        "external_exam_block": ("high", "no_exams", "partial_day"),
        "memorial_event": ("medium", "informational", "none"),
        "informational_event": ("low", "informational", "none"),
        "unknown": ("medium", "informational", "none"),
    }
    relevance, constraint, scope = defaults[event_type]
    return {
        "scheduling_relevance": relevance,
        "constraint_type": constraint,
        "block_scope": scope,
    }


def classify_candidate(candidate: dict) -> tuple[str, dict, float]:
    source_text = candidate["source_text"]
    text = source_text.lower()

    if "היום הראשון" in source_text and ("לימודים" in source_text or "סמסטר" in source_text):
        event_type, confidence = "semester_start", 0.95
    elif "היום האחרון" in source_text and "סמסטר" in source_text:
        event_type, confidence = "semester_end", 0.95
    elif "ימי היערכות לבחינות" in source_text:
        event_type, confidence = "exam_prep_period", 0.92
    elif "תקופת בחינות" in source_text or "תחילת תקופת הבחינות" in source_text:
        event_type, confidence = "exam_period", 0.92
    elif "פסיכומטר" in source_text:
        event_type, confidence = "psychometric_block", 0.95
    elif "סמסטר ראשון בתיכון" in source_text or "בחינות" in source_text and "אין לשבץ" in source_text:
        event_type, confidence = "external_exam_block", 0.84
    elif "האוניברסיטה סגורה" in source_text:
        event_type, confidence = "university_closed", 0.93
    elif "אין לימודים" in source_text:
        event_type, confidence = "no_studies_day", 0.90
    elif "הפסקת לימודים" in source_text:
        event_type, confidence = "partial_block", 0.88
    elif "יסתיימו בשעה" in source_text:
        event_type, confidence = "reduced_hours_day", 0.88
    elif "יום הסטודנט" in source_text:
        event_type, confidence = "partial_block", 0.90
    elif "יום פתוח" in source_text:
        event_type, confidence = "open_day", 0.85
    elif "אוריינטציה" in source_text:
        event_type, confidence = "orientation_day", 0.85
    elif "יום השלמה" in source_text:
        event_type, confidence = "makeup_day", 0.85
    elif any(k in source_text for k in ["טקס", "עצרת", "יום הזיכרון", "יום העצמאות", "תשעה באב"]):
        event_type, confidence = "memorial_event", 0.78
    elif "חופשת" in source_text:
        event_type, confidence = "holiday", 0.75
    else:
        event_type, confidence = "unknown", 0.45

    if candidate.get("in_no_exam_section") and event_type in {"holiday", "informational_event", "unknown"}:
        event_type = "external_exam_block"
        confidence = max(confidence, 0.72)

    shape = _default_shape(event_type, bool(candidate.get("end_date")))

    if candidate.get("start_time") or candidate.get("end_time"):
        shape["block_scope"] = "partial_day"
        if event_type in {"external_exam_block", "partial_block", "reduced_hours_day"}:
            pass
        elif event_type in {"unknown", "informational_event"}:
            event_type = "partial_block"
            shape = _default_shape(event_type, bool(candidate.get("end_date")))
        if candidate.get("start_time") and not candidate.get("end_time"):
            shape["constraint_type"] = "no_exam_after_time"

    if event_type == "exam_period" and not candidate.get("end_date") and "תחילת" in source_text:
        candidate["notes"] = "missing end date"
        candidate["requires_manual_review"] = True

    if event_type not in EVENT_TYPES:
        event_type = "unknown"

    return event_type, shape, confidence


def classify_candidates(candidates: list[dict]) -> list[ExtractedRecord]:
    records: list[ExtractedRecord] = []
    for candidate in candidates:
        event_type, shape, confidence = classify_candidate(candidate)

        inferred_semester = candidate.get("semester_context") or detect_semester_from_text(candidate["source_text"])

        requires_manual_review = bool(candidate.get("requires_manual_review", False))
        notes = candidate.get("notes")

        if event_type == "unknown" and shape["scheduling_relevance"] == "high":
            requires_manual_review = True
        if event_type == "unknown":
            requires_manual_review = True

        records.append(
            ExtractedRecord(
                event_name=candidate.get("event_name") or candidate["source_text"],
                event_type=event_type,
                semester=inferred_semester,
                start_date=candidate["start_date"],
                end_date=candidate.get("end_date"),
                is_range=bool(candidate.get("end_date")),
                scheduling_relevance=shape["scheduling_relevance"],
                constraint_type=shape["constraint_type"],
                block_scope=shape["block_scope"],
                start_time=candidate.get("start_time"),
                end_time=candidate.get("end_time"),
                source_text=candidate["source_text"],
                notes=notes,
                requires_manual_review=requires_manual_review,
                confidence_score=confidence,
            )
        )
    return records
