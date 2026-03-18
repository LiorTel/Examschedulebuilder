# Exam Schedule Builder - Phase A MVP

This project implements **Phase A** of an exam-scheduling system: ingesting an academic calendar, extracting and classifying events, allowing user review/editing, validating required constraints, and saving approved structured records.

## What is included

- Upload one academic calendar file (`PDF`, `DOCX`, `XLSX`, `CSV`)
- Require academic year input
- Parse raw text and table rows
- Extract dates and date ranges with source trace text
- Classify extracted events into predefined event types
- Editable review table (edit/delete/add rows)
- Validation before approval:
  - `moed_a_start` and `moed_a_end` required
  - `moed_b_start` and `moed_b_end` required
  - valid dates
  - `start_date <= end_date` when `end_date` exists
- Save approved calendar/events to SQLite
- Placeholder section for future phases (B/C)

## Architecture

- `app.py`: Streamlit UI and UX flow for upload → processing → review → validation → approval
- `phase_a/parsers.py`: document parsing layer
- `phase_a/extraction.py`: date and range extraction layer
- `phase_a/classifier.py`: event-type classification layer
- `phase_a/validation.py`: business-rule validation layer
- `phase_a/storage.py`: persistence layer (SQLite)
- `phase_a/service.py`: orchestration layer for Phase A processing

## Data model

Persisted entities in SQLite:

- `academic_calendars`
  - `id`
  - `academic_year`
  - `source_file_name`
  - `status`
  - `created_at`
  - `updated_at`

- `academic_calendar_events`
  - `id`
  - `calendar_id`
  - `event_type`
  - `start_date`
  - `end_date`
  - `source_text`
  - `confidence_score`
  - `notes`
  - `created_at`
  - `updated_at`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL and follow:
1. Upload file + enter academic year
2. Review extracted rows
3. Edit/add/delete rows as needed
4. Validate
5. Approve and save

## Run tests

```bash
pytest -q
```

## Notes

- This MVP intentionally implements **Phase A only**.
- Scheduling/optimization logic is not implemented yet and is left as a future phase.
