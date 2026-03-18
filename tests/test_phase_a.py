from phase_a.classifier import classify_candidates
from phase_a.extraction import extract_date_candidates
from phase_a.validation import validate_events


def test_extract_hebrew_ranges_and_month_name():
    blocks = [
        {"text": "ימי היערכות לבחינות. אין לימודים בימים אלה 26-27.1.26", "semester_context": "A", "in_no_exam_section": False},
        {"text": "בחינה פסיכומטרית מרץ: 29-30 במרץ 2026", "semester_context": "B", "in_no_exam_section": True},
    ]
    candidates = extract_date_candidates(blocks, "2025-2026")
    assert len(candidates) == 2
    assert candidates[0]["start_date"].isoformat() == "2026-01-26"
    assert candidates[0]["end_date"].isoformat() == "2026-01-27"
    assert candidates[1]["start_date"].isoformat() == "2026-03-29"
    assert candidates[1]["end_date"].isoformat() == "2026-03-30"


def test_classification_semantic_hebrew_examples():
    candidates = [
        {
            "event_name": "היום הראשון ללימודים – סמסטר א'",
            "source_text": "היום הראשון ללימודים – סמסטר א' 26.10.25",
            "start_date": __import__("datetime").date(2025, 10, 26),
            "end_date": None,
            "semester_context": "A",
            "in_no_exam_section": False,
            "start_time": None,
            "end_time": None,
        },
        {
            "event_name": "יום הסטודנט",
            "source_text": "יום הסטודנט (הפסקת לימודים משעה 16:00) 4.6.26",
            "start_date": __import__("datetime").date(2026, 6, 4),
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
