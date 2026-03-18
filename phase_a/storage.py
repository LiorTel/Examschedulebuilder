from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path("data/academic_calendar.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS academic_calendars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                academic_year TEXT NOT NULL,
                source_file_name TEXT NOT NULL,
                source_file_type TEXT NOT NULL,
                source_file_size INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS academic_calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calendar_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                source_text TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(calendar_id) REFERENCES academic_calendars(id)
            );
            """
        )


def save_calendar(academic_year: str, source_file_name: str, source_file_type: str, source_file_size: int, rows: list[dict]) -> int:
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO academic_calendars (academic_year, source_file_name, source_file_type, source_file_size, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (academic_year, source_file_name, source_file_type, source_file_size, "approved", now, now),
        )
        calendar_id = cursor.lastrowid

        for row in rows:
            conn.execute(
                """
                INSERT INTO academic_calendar_events (
                    calendar_id, event_type, start_date, end_date, source_text,
                    confidence_score, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    calendar_id,
                    row.get("event_type", "unknown"),
                    row.get("start_date"),
                    row.get("end_date") or None,
                    row.get("source_text", ""),
                    float(row.get("confidence_score") or 0.0),
                    row.get("notes") or None,
                    now,
                    now,
                ),
            )

    return int(calendar_id)
