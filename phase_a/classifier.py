from __future__ import annotations

from phase_a.models import EVENT_TYPES, ExtractedRecord


KEYWORD_MAP = {
    "semester_a_start": ["semester a start", "start of semester a", "תחילת סמסטר א"],
    "semester_a_end": ["semester a end", "end of semester a", "סיום סמסטר א"],
    "semester_b_start": ["semester b start", "start of semester b", "תחילת סמסטר ב"],
    "semester_b_end": ["semester b end", "end of semester b", "סיום סמסטר ב"],
    "moed_a_start": ["moed a start", "exam period a starts", "תחילת מועד א"],
    "moed_a_end": ["moed a end", "exam period a ends", "סיום מועד א"],
    "moed_b_start": ["moed b start", "exam period b starts", "תחילת מועד ב"],
    "moed_b_end": ["moed b end", "exam period b ends", "סיום מועד ב"],
    "holiday": ["holiday", "חג"],
    "no_studies_day": ["no studies", "no classes", "אין לימודים"],
    "vacation": ["vacation", "break", "חופשה"],
}


def classify_candidate(source_text: str) -> tuple[str, float]:
    lowered = source_text.lower()
    for event_type, keywords in KEYWORD_MAP.items():
        if any(keyword in lowered for keyword in keywords):
            return event_type, 0.90
    return "unknown", 0.55


def classify_candidates(candidates: list[dict]) -> list[ExtractedRecord]:
    records: list[ExtractedRecord] = []
    for candidate in candidates:
        event_type, confidence = classify_candidate(candidate["source_text"])
        if event_type not in EVENT_TYPES:
            event_type = "unknown"
        records.append(
            ExtractedRecord(
                source_text=candidate["source_text"],
                start_date=candidate["start_date"],
                end_date=candidate.get("end_date"),
                event_type=event_type,
                confidence_score=confidence,
            )
        )
    return records
