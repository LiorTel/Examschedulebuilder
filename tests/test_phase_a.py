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
    assert blocks[0]["lines"][1] == "מ- 28.1.26 עד 13.3.26"
    assert "י' בשבט" in blocks[0]["text"]


def test_extract_preserves_multiline_notes_in_block():
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
        }
    ]
    candidates = extract_date_candidates(blocks, "2025-2026")
    assert len(candidates) == 1
    assert candidates[0]["start_date"].isoformat() == "2026-01-28"
    assert candidates[0]["end_date"].isoformat() == "2026-03-13"
    assert candidates[0]["notes"] == "ימים ד' - ו'; י' בשבט עד כ\"ד באדר"


def test_classification_semantic_hebrew_examples():
    candidates = [
        {
            "event_name": "היום הראשון ללימודים – סמסטר א'",
            "source_text": "היום הראשון ללימודים – סמסטר א' 26.10.25",
            "start_date": date(2025, 10, 26),
            "end_date": None,
            "semester_context": "A",
            "in_no_exam_section": False,
            "start_time": None,
            "end_time": None,
        },
        {
            "event_name": "יום הסטודנט",
            "source_text": "יום הסטודנט (הפסקת לימודים משעה 16:00) 4.6.26",
            "start_date": date(2026, 6, 4),
            "end_date": None,
            "semester_context": "B",
            "in_no_exam_section": False,
            "start_time": "16:00",
            "end_time": None,
        },
    ]
    records = classify_candidates(candidates)
    assert records[0].event_type == "semester_start"
    assert records[0].semester == "A"
    assert records[1].event_type == "partial_block"
    assert records[1].block_scope == "partial_day"


def test_validate_semester_and_manual_review_rules():
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
            "block_scope": "full_day",
            "scheduling_relevance": "high",
            "requires_manual_review": False,
            "start_time": "",
            "end_time": "",
        },
    ]
    errors = validate_events(rows)
    assert any("Missing semester A end" in err for err in errors)
    assert any("requires manual review" in err for err in errors)
