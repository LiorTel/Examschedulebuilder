from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional


EVENT_TYPES = [
    "semester_a_start",
    "semester_a_end",
    "semester_b_start",
    "semester_b_end",
    "moed_a_start",
    "moed_a_end",
    "moed_b_start",
    "moed_b_end",
    "holiday",
    "no_studies_day",
    "vacation",
    "unknown",
]


@dataclass
class ExtractedRecord:
    source_text: str
    start_date: date
    end_date: Optional[date]
    event_type: str
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
