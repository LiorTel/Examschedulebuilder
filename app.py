from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from phase_a.models import EVENT_TYPES
from phase_a.service import process_calendar_file
from phase_a.storage import init_db, save_calendar
from phase_a.validation import validate_events

st.set_page_config(page_title="Exam Scheduler - Phase A", layout="wide")
init_db()

st.title("Exam Scheduling System - Phase A")
st.caption("Upload and approve an academic calendar (ingestion + review only).")

if "processed_rows" not in st.session_state:
    st.session_state.processed_rows = []
if "source_file_name" not in st.session_state:
    st.session_state.source_file_name = None
if "academic_year" not in st.session_state:
    st.session_state.academic_year = None
if "source_file_type" not in st.session_state:
    st.session_state.source_file_type = None
if "source_file_size" not in st.session_state:
    st.session_state.source_file_size = None

with st.container(border=True):
    st.subheader("1) Upload academic calendar")
    with st.form("upload_form"):
        academic_year = st.text_input("Academic year (required)", placeholder="2025-2026")
        upload = st.file_uploader("Upload one file", type=["pdf", "docx", "xlsx", "csv"])
        submitted = st.form_submit_button("Process file")

        if submitted:
            if not academic_year.strip():
                st.error("Academic year is required.")
            elif not upload:
                st.error("Please upload one file.")
            else:
                file_bytes = upload.getvalue()
                if not file_bytes:
                    st.error("Uploaded file is empty.")
                else:
                    with st.spinner("Processing file..."):
                        rows = process_calendar_file(upload.name, file_bytes, academic_year.strip())
                    st.session_state.processed_rows = rows
                    st.session_state.source_file_name = upload.name
                    st.session_state.source_file_type = upload.type or "unknown"
                    st.session_state.source_file_size = len(file_bytes)
                    st.session_state.academic_year = academic_year.strip()
                    st.success(f"Extracted {len(rows)} records from {upload.name}.")

if st.session_state.processed_rows:
    st.subheader("2) Review extracted events")

    df = pd.DataFrame(st.session_state.processed_rows)
    if "notes" not in df.columns:
        df["notes"] = ""

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "event_type": st.column_config.SelectboxColumn(options=EVENT_TYPES),
            "confidence_score": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05),
            "start_date": st.column_config.TextColumn(help="ISO date format: YYYY-MM-DD"),
            "end_date": st.column_config.TextColumn(help="Optional ISO date: YYYY-MM-DD"),
            "source_text": st.column_config.TextColumn(width="large"),
        },
    )

    st.session_state.processed_rows = edited_df.fillna("").to_dict(orient="records")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Validate calendar"):
            errors = validate_events(st.session_state.processed_rows)
            if errors:
                st.error("Validation errors found:")
                for error in errors:
                    st.write(f"- {error}")
            else:
                st.success("Validation passed. You can approve the calendar.")

    with col2:
        if st.button("Approve and save"):
            errors = validate_events(st.session_state.processed_rows)
            if errors:
                st.error("Cannot approve. Fix validation issues first.")
            else:
                calendar_id = save_calendar(
                    academic_year=st.session_state.academic_year,
                    source_file_name=st.session_state.source_file_name,
                    source_file_type=st.session_state.source_file_type,
                    source_file_size=st.session_state.source_file_size,
                    rows=st.session_state.processed_rows,
                )
                st.success(f"Academic calendar approved and saved (id={calendar_id}).")

with st.expander("Phase B/C placeholders"):
    st.info(
        "Scheduling optimization, conflict resolution, and final exam timetable generation "
        "will be added in later phases."
    )

uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
