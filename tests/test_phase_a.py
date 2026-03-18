from datetime import date

from phase_a.classifier import classify_candidates
from phase_a.extraction import extract_date_candidates
from phase_a.parsers import _build_blocks
from phase_a.validation import validate_events


def test_parser_groups_multiline_event_block():
    lines = [
        "סמסטר א'",
        "תקופת בחינות סמסטר א'",
        "מ- 28.1.26 עד 13.3.26",
        "ימים ד' – ו'",
        "י' בשבט עד כ\"ד באדר",
        "היום הראשון לסמסטר ב'",
        "12.4.26",
    ]
    blocks = _build_blocks(lines)
    assert len(blocks) == 2
    assert blocks[0]["title"] == "תקופת בחינות סמסטר א'"
    assert blocks[0]["semester_context"] == "A"
    assert "י' בשבט" in blocks[0]["text"]


def test_extract_multiline_exam_period_with_notes():
    blocks = [
        {
            "title": "תקופת בחינות סמסטר א'",
            "lines": [
                "תקופת בחינות סמסטר א'",
                "מ- 28.1.26 עד 13.3.26",
                "ימים ד' – ו'",
                "י' בשבט עד כ\"ד באדר",
            ],
            "text": "תקופת בחינות סמסטר א'\nמ- 28.1.26 עד 13.3.26\nימים ד' – ו'\nי' בשבט עד כ\"ד באדר",
            "semester_context": "A",
            "in_no_exam_section": False,
            "section_context": "GENERAL",
        }
    ]
    candidates = extract_date_candidates(blocks, "2025-2026")
    assert len(candidates) == 1
    assert candidates[0]["start_date"].isoformat() == "2026-01-28"
    assert candidates[0]["end_date"].isoformat() == "2026-03-13"
    assert candidates[0]["notes"] == "ימים ד' - ו'; י' בשבט עד כ\"ד באדר"


def test_extract_external_exam_two_dates_with_partial_time_on_second():
    blocks = [
        {
            "title": 'בחינות "סמסטר ראשון בתיכון"',
            "lines": [
                'בחינות "סמסטר ראשון בתיכון": 20.3.26 (יום ו\'), 26.3.26 (יום ה\') החל משעה 14:00'
            ],
            "text": 'בחינות "סמסטר ראשון בתיכון": 20.3.26 (יום ו\'), 26.3.26 (יום ה\') החל משעה 14:00',
            "semester_context": "B",
            "in_no_exam_section": True,
            "section_context": "אין לשבץ בחינות",
        }
    ]
    candidates = extract_date_candidates(blocks, "2025-2026")
    assert len(candidates) == 2
    assert candidates[0]["start_date"].isoformat() == "2026-03-20"
    assert candidates[0]["start_time"] is None
    assert candidates[1]["start_date"].isoformat() == "2026-03-26"
    assert candidates[1]["start_time"] == "14:00"


def test_classify_open_ended_exam_period_requires_manual_review():
    candidates = [
        {
            "event_name": "תחילת תקופת הבחינות – סמסטר ב'",
            "source_text": "תחילת תקופת הבחינות – סמסטר ב' 8.7.26",
            "start_date": date(2026, 7, 8),
            "end_date": None,
            "semester_context": "B",
            "in_no_exam_section": False,
            "section_context": "GENERAL",
            "start_time": None,
            "end_time": None,
            "notes": None,
        }
    ]
    records = classify_candidates(candidates)
    assert records[0].event_type == "exam_period"
    assert records[0].semester == "B"
    assert records[0].is_range is True
    assert records[0].is_open_ended is True
    assert records[0].requires_manual_review is True


def test_classification_core_examples():
    candidates = [
        {
            "event_name": "יום אוריינטציה",
            "source_text": "יום אוריינטציה לתלמידי שנה א' בתואר ראשון יתקיים בתאריך 23.10.2025",
            "start_date": date(2025, 10, 23),
            "end_date": None,
            "semester_context": "A",
            "in_no_exam_section": False,
            "section_context": "GENERAL",
            "start_time": None,
            "end_time": None,
            "notes": None,
        },
        {
            "event_name": "חופשת פורים",
            "source_text": "חופשת פורים – האוניברסיטה סגורה 3.3.26",
            "start_date": date(2026, 3, 3),
            "end_date": None,
            "semester_context": "A",
            "in_no_exam_section": False,
            "section_context": "GENERAL",
            "start_time": None,
            "end_time": None,
            "notes": None,
        },
    ]
    records = classify_candidates(candidates)
    assert records[0].event_type == "orientation_day"
    assert records[1].event_type == "university_closed"
    assert records[1].constraint_type == "no_exams"


def test_validation_rules_new_phase_a():
    rows = [
        {
            "event_type": "semester_start",
            "semester": "A",
            "start_date": "2025-10-26",
            "end_date": "",
            "block_scope": "none",
            "scheduling_relevance": "high",
            "requires_manual_review": False,
            "start_time": "",
            "end_time": "",
        },
        {
            "event_type": "exam_period",
            "semester": "B",
            "start_date": "2026-07-08",
            "end_date": "",
            "block_scope": "date_range",
            "scheduling_relevance": "high",
            "requires_manual_review": False,
            "start_time": "",
            "end_time": "",
        },
    ]
    errors = validate_events(rows)
    assert any("Missing semester A end" in err for err in errors)
    assert any("open-ended exam period B" in err for err in errors)
