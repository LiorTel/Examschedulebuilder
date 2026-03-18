from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


EVENT_TYPES = [
    "semester_start",
    "semester_end",
    "exam_prep_period",
    "exam_period",
    "orientation_day",
    "open_day",
    "university_closed",
    "no_studies_day",
    "partial_block",
    "reduced_hours_day",
    "makeup_day",
    "psychometric_block",
    "external_exam_block",
    "informational_event",
    "holiday",
    "unknown",
]

SEMESTERS = ["A", "B", "SUMMER", "NEXT_YEAR", "NONE"]
SCHEDULING_RELEVANCE = ["high", "medium", "low"]
CONSTRAINT_TYPES = ["no_exams", "no_classes", "reduced_hours", "no_exam_after_time", "informational"]
BLOCK_SCOPES = ["full_day", "date_range", "partial_day", "none"]


@dataclass
class ExtractedRecord:
    event_name: str
    event_type: str
    semester: str
    start_date: date
    end_date: date | None
    is_range: bool
    is_open_ended: bool
    constraint_type: str
    scheduling_relevance: str
    block_scope: str
    start_time: str | None
    end_time: str | None
    requires_manual_review: bool
    notes: str | None
    source_text: str
    confidence_score: float

    def to_row(self) -> dict:
        row = asdict(self)
        row["start_date"] = self.start_date.isoformat() if self.start_date else None
        row["end_date"] = self.end_date.isoformat() if self.end_date else None
        return row


@dataclass
class AcademicCalendar:
    id: int | None
    academic_year: str
    source_file_name: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class AcademicCalendarEvent:
    id: int | None
    calendar_id: int
    event_type: str
    start_date: date
    end_date: date | None
    source_text: str
    confidence_score: float
    notes: str | None
    created_at: datetime
    updated_at: datetime
