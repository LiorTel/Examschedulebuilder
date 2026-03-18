from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from docx import Document
from pypdf import PdfReader

from phase_a.hebrew_utils import detect_semester_from_text, normalize_hebrew_text


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv"}
DATE_HINT_PATTERN = re.compile(r"\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\b(?:ב)?(?:ינואר|פברואר|מרץ|מרס|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)\b")


@dataclass
class ParsedDocument:
    raw_text: str
    table_rows: list[str]
    blocks: list[dict]


def _table_rows_from_dataframe(df: pd.DataFrame) -> Iterable[str]:
    for _, row in df.fillna("").iterrows():
        values = [str(v).strip() for v in row.tolist() if str(v).strip()]
        if values:
            yield " | ".join(values)


def _build_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    current_semester = None
    in_no_exam_section = False
    i = 0

    while i < len(lines):
        line = normalize_hebrew_text(lines[i])
        if not line:
            i += 1
            continue

        heading_semester = detect_semester_from_text(line)
        if heading_semester and len(line.split()) <= 4:
            current_semester = heading_semester
            if "אין לשבץ בחינות" not in line:
                in_no_exam_section = False

        if "אין לשבץ בחינות" in line:
            in_no_exam_section = True

        combined = line
        if i + 1 < len(lines):
            nxt = normalize_hebrew_text(lines[i + 1])
            if nxt and (DATE_HINT_PATTERN.search(nxt) and not DATE_HINT_PATTERN.search(line)):
                combined = normalize_hebrew_text(f"{line} {nxt}")
                i += 1

        block_semester = detect_semester_from_text(combined) or current_semester
        blocks.append(
            {
                "text": combined,
                "semester_context": block_semester,
                "in_no_exam_section": in_no_exam_section,
            }
        )

        if re.match(r"^[א-ת\s]+:$", combined) and "אין לשבץ בחינות" not in combined:
            in_no_exam_section = False

        i += 1

    return blocks


def parse_uploaded_file(file_name: str, file_bytes: bytes) -> ParsedDocument:
    extension = Path(file_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")
    if not file_bytes:
        raise ValueError("Uploaded file is empty")

    if extension == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        raw_text = "\n".join(pages)
        table_rows: list[str] = []
    elif extension == ".docx":
        doc = Document(io.BytesIO(file_bytes))
        raw_text = "\n".join(p.text for p in doc.paragraphs)
        table_rows = []
        for table in doc.tables:
            for row in table.rows:
                values = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if values:
                    table_rows.append(" | ".join(values))
    elif extension == ".xlsx":
        workbook = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
        table_rows = []
        blocks = []
        for sheet_name, df in workbook.items():
            blocks.append(f"Sheet: {sheet_name}")
            parsed_rows = list(_table_rows_from_dataframe(df))
            blocks.extend(parsed_rows)
            table_rows.extend(parsed_rows)
        raw_text = "\n".join(blocks)
    else:  # .csv
        df = pd.read_csv(io.BytesIO(file_bytes))
        table_rows = list(_table_rows_from_dataframe(df))
        raw_text = "\n".join(table_rows)

    lines = [ln for ln in raw_text.splitlines() if ln.strip()]
    blocks = _build_blocks(lines)
    return ParsedDocument(raw_text=raw_text, table_rows=table_rows, blocks=blocks)
