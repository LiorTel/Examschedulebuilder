from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv"}


@dataclass
class ParsedDocument:
    raw_text: str
    table_rows: list[str]


def _table_rows_from_dataframe(df: pd.DataFrame) -> Iterable[str]:
    for _, row in df.fillna("").iterrows():
        values = [str(v).strip() for v in row.tolist() if str(v).strip()]
        if values:
            yield " | ".join(values)


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
            blocks.extend(list(_table_rows_from_dataframe(df)))
            table_rows.extend(list(_table_rows_from_dataframe(df)))
        raw_text = "\n".join(blocks)
    else:  # .csv
        df = pd.read_csv(io.BytesIO(file_bytes))
        table_rows = list(_table_rows_from_dataframe(df))
        raw_text = "\n".join(table_rows)

    return ParsedDocument(raw_text=raw_text, table_rows=table_rows)
