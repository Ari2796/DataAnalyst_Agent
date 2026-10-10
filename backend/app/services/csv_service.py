"""CSV ingestion, validation, and encoding resilience service."""

import io
import re
import uuid
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
import pandas as pd
from app.config import settings

ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]


class CSVService:
    """Safely ingests and parses user-supplied CSV files."""

    @staticmethod
    def sanitize_column_name(col: str) -> str:
        """Sanitizes column name to prevent malicious tokens or control characters."""
        cleaned = str(col).strip()
        # Replace non-printable characters and control chars
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)
        # Ensure column is not empty after stripping
        return cleaned if cleaned else "unnamed_column"

    @classmethod
    async def process_upload(cls, file: UploadFile) -> Tuple[str, pd.DataFrame, int]:
        """Validates and parses uploaded CSV into a pandas DataFrame.
        
        Returns:
            Tuple[dataset_id, DataFrame, file_size_bytes]
        """
        # 1. Validate file extension
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a valid filename."
            )

        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension for '{file.filename}'. Only .csv files are supported."
            )

        # 2. Read bytes and check size
        contents = await file.read()
        file_size = len(contents)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes). Please upload a valid CSV with rows."
            )

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=(
                    f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit "
                    f"of {settings.max_upload_size_mb} MB."
                )
            )

        # 3. Try parsing with multiple encodings
        df: pd.DataFrame | None = None
        last_error: Exception | None = None

        for encoding in ENCODINGS_TO_TRY:
            try:
                buffer = io.BytesIO(contents)
                df = pd.read_csv(
                    buffer,
                    encoding=encoding,
                    sep=None,  # Sniff delimiter (comma, semicolon, tab)
                    engine="python",
                    on_bad_lines="skip",  # Resilient to malformed rows
                )
                break
            except Exception as e:
                last_error = e
                continue

        if df is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Could not parse CSV file '{file.filename}'. Ensure it is a valid delimiter-separated text file. "
                    f"Details: {str(last_error)}"
                )
            )

        if df.empty or len(df.columns) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded CSV has no parseable rows or columns."
            )

        # 4. Clean column names
        df.columns = [cls.sanitize_column_name(c) for c in df.columns]

        # Ensure unique column names if duplicates exist after cleaning
        seen = {}
        new_cols = []
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols

        dataset_id = str(uuid.uuid4())
        return dataset_id, df, file_size
