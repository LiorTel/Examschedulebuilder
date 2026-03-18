from phase_a.classifier import classify_candidates
from phase_a.extraction import extract_date_candidates
from phase_a.validation import validate_events


def test_extract_date_candidates_single_and_range():
    text = """
    Moed A start 12/01/2026
    Moed B window 13/02/2026 - 20/02/2026
    """
    candidates = extract_date_candidates(text, "2025-2026")
    assert len(candidates) == 2
    assert candidates[0]["end_date"] is None
    assert candidates[1]["end_date"] is not None


def test_classify_candidates():
    candidates = [
        {"source_text": "Moed A start 12/01/2026", "start_date": "2026-01-12", "end_date": None},
        {"source_text": "Random event 12/01/2026", "start_date": "2026-01-12", "end_date": None},
    ]
    records = classify_candidates(candidates)
    assert records[0].event_type == "moed_a_start"
    assert records[1].event_type == "unknown"


def test_validate_events_required_and_ranges():
    rows = [
        {"event_type": "moed_a_start", "start_date": "2026-01-01", "end_date": "2026-01-05"},
        {"event_type": "moed_a_end", "start_date": "2026-01-06", "end_date": ""},
        {"event_type": "moed_b_start", "start_date": "2026-02-01", "end_date": ""},
        {"event_type": "moed_b_end", "start_date": "2026-01-20", "end_date": "2026-01-19"},
    ]
    errors = validate_events(rows)
    assert any("start_date cannot be after end_date" in err for err in errors)
