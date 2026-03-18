from __future__ import annotations

import re


HEBREW_MONTHS = {
    "ינואר": 1,
    "פברואר": 2,
    "מרץ": 3,
    "מרס": 3,
    "אפריל": 4,
    "מאי": 5,
    "יוני": 6,
    "יולי": 7,
    "אוגוסט": 8,
    "ספטמבר": 9,
    "אוקטובר": 10,
    "נובמבר": 11,
    "דצמבר": 12,
}


def normalize_hebrew_text(text: str) -> str:
    normalized = text.replace("\u2013", "-").replace("\u2014", "-").replace("־", "-")
    normalized = re.sub(r"[\t\r]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace(" :", ":")
    return normalized.strip()


def detect_semester_from_text(text: str) -> str | None:
    if "סמסטר א" in text:
        return "A"
    if "סמסטר ב" in text:
        return "B"
    if "סמסטר קיץ" in text:
        return "SUMMER"
    if "פתיחת שנה" in text or "תשפ" in text:
        return "NEXT_YEAR"
    return None
