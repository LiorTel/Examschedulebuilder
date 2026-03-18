from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Optional


EVENT_TYPES = [
    "semester_start",
    "semester_end",
    "exam_prep_period",
    "exam_period",
    "holiday",
    "university_closed",
    "no_studies_day",
    "partial_block",
    "reduced_hours_day",
    "open_day",
    "orientation_day",
    "makeup_day",
    "psychometric_block",
    "external_exam_block",
    "memorial_event",
    "informational_event",
    "unknown",
]

SEMESTERS = ["A", "B", "SUMMER", "NEXT_YEAR", None]
SCHEDULING_RELEVANCE = ["high", "medium", "low"]
CONSTRAINT_TYPES = ["no_exams", "no_classes", "reduced_hours", "no_exam_after_time", "informational"]
BLOCK_SCOPES = ["full_day", "date_range", "partial_day", "none"]


@dataclass
class ExtractedRecord:
    event_name: str
    event_type: str
    semester: Optional[str]
    start_date: date
    end_date: Optional[date]
    is_range: bool
    scheduling_relevance: str
    constraint_type: str
    block_scope: str
    start_time: Optional[str]
    end_time: Optional[str]
    source_text: str
    notes: Optional[str]
    requires_manual_review: bool
    confidence_score: float

    def to_row(self) -> dict:
        row = asdict(self)
        row["start_date"] = self.start_date.isoformat() if self.start_date else None
        row["end_date"] = self.end_date.isoformat() if self.end_date else None
        return row


@dataclass
class AcademicCalendar:
    id: Optional[int]
    academic_year: str
    source_file_name: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class AcademicCalendarEvent:
    id: Optional[int]
    calendar_id: int
    event_type: str
    start_date: date
    end_date: Optional[date]
    source_text: str
    confidence_score: float
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
