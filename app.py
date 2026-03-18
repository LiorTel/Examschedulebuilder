from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from phase_a.models import BLOCK_SCOPES, CONSTRAINT_TYPES, EVENT_TYPES, SCHEDULING_RELEVANCE, SEMESTERS
from phase_a.service import process_calendar_file
from phase_a.storage import init_db, save_calendar
from phase_a.validation import validate_events

st.set_page_config(page_title="Exam Scheduler - Phase A", layout="wide")
init_db()

st.title("Exam Scheduling System - Phase A")
st.caption("Hebrew academic calendar ingestion, semantic extraction, review, validation, and approval.")

for key, default in {
    "processed_rows": [],
    "source_file_name": None,
    "academic_year": None,
    "source_file_type": None,
    "source_file_size": None,
    "debug_raw_blocks": [],
    "debug_candidates": [],
    "debug_classified": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
                    with st.spinner("Processing Hebrew academic calendar..."):
                        result = process_calendar_file(upload.name, file_bytes, academic_year.strip())
                    st.session_state.processed_rows = result["rows"]
                    st.session_state.debug_raw_blocks = result["raw_blocks"]
                    st.session_state.debug_candidates = result["candidates"]
                    st.session_state.debug_classified = result["classified"]
                    st.session_state.source_file_name = upload.name
                    st.session_state.source_file_type = upload.type or "unknown"
                    st.session_state.source_file_size = len(file_bytes)
                    st.session_state.academic_year = academic_year.strip()
                    st.success(f"Extracted {len(result['rows'])} structured records from {upload.name}.")

if st.session_state.processed_rows:
    st.subheader("2) Review extracted events")

    df = pd.DataFrame(st.session_state.processed_rows)
    for col, default in {
        "event_name": "",
        "event_type": "unknown",
        "semester": None,
        "start_date": "",
        "end_date": "",
        "is_range": False,
        "scheduling_relevance": "medium",
        "constraint_type": "informational",
        "block_scope": "none",
        "start_time": "",
        "end_time": "",
        "source_text": "",
        "notes": "",
        "requires_manual_review": False,
        "confidence_score": 0.0,
    }.items():
        if col not in df.columns:
            df[col] = default

    f1, f2, f3 = st.columns(3)
    with f1:
        semester_filter = st.multiselect("Filter semester", ["A", "B", "SUMMER", "NEXT_YEAR"], default=[])
    with f2:
        relevance_filter = st.multiselect("Filter relevance", SCHEDULING_RELEVANCE, default=[])
    with f3:
        review_only = st.checkbox("Only requires manual review", value=False)

    filtered_df = df.copy()
    if semester_filter:
        filtered_df = filtered_df[filtered_df["semester"].isin(semester_filter)]
    if relevance_filter:
        filtered_df = filtered_df[filtered_df["scheduling_relevance"].isin(relevance_filter)]
    if review_only:
        filtered_df = filtered_df[filtered_df["requires_manual_review"] == True]

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "event_type": st.column_config.SelectboxColumn(options=EVENT_TYPES),
            "semester": st.column_config.SelectboxColumn(options=SEMESTERS),
            "scheduling_relevance": st.column_config.SelectboxColumn(options=SCHEDULING_RELEVANCE),
            "constraint_type": st.column_config.SelectboxColumn(options=CONSTRAINT_TYPES),
            "block_scope": st.column_config.SelectboxColumn(options=BLOCK_SCOPES),
            "confidence_score": st.column_config.NumberColumn(min_value=0.0, max_value=1.0, step=0.05),
            "requires_manual_review": st.column_config.CheckboxColumn(),
            "is_range": st.column_config.CheckboxColumn(),
            "start_date": st.column_config.TextColumn(help="ISO date format: YYYY-MM-DD"),
            "end_date": st.column_config.TextColumn(help="Optional ISO date: YYYY-MM-DD"),
            "start_time": st.column_config.TextColumn(help="HH:MM"),
            "end_time": st.column_config.TextColumn(help="HH:MM"),
            "event_name": st.column_config.TextColumn(width="large"),
            "source_text": st.column_config.TextColumn(width="large"),
            "notes": st.column_config.TextColumn(width="large"),
        },
    )

    preserved = df.copy()
    if len(edited_df) != len(df):
        st.session_state.processed_rows = edited_df.fillna("").to_dict(orient="records")
    else:
        preserved.update(edited_df)
        st.session_state.processed_rows = preserved.fillna("").to_dict(orient="records")

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

    with st.expander("Debug: parsing & extraction pipeline"):
        st.markdown("**Raw parsed blocks**")
        st.dataframe(pd.DataFrame(st.session_state.debug_raw_blocks), use_container_width=True)
        st.markdown("**Extracted candidates (pre-classification)**")
        st.dataframe(pd.DataFrame(st.session_state.debug_candidates), use_container_width=True)
        st.markdown("**Classification output**")
        st.dataframe(pd.DataFrame(st.session_state.debug_classified), use_container_width=True)

with st.expander("Phase B/C placeholders"):
    st.info(
        "Scheduling optimization, conflict resolution, and final exam timetable generation "
        "will be added in later phases."
    )

uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
