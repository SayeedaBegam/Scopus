"""
Persistent storage helpers for manual collaboration records and generated Excel files.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from utils.manual_processor import MANUAL_COLUMNS, normalize_manual_dataframe


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MANUAL_RECORDS_FILE = DATA_DIR / "manual_professor_records.csv"
GENERATED_REPORTS_DIR = DATA_DIR / "generated_reports"


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_manual_records() -> pd.DataFrame:
    ensure_storage()
    if not MANUAL_RECORDS_FILE.exists():
        return pd.DataFrame(columns=MANUAL_COLUMNS)

    df = pd.read_csv(MANUAL_RECORDS_FILE, dtype=str).fillna("")
    return normalize_manual_dataframe(df)


def save_manual_records(df: pd.DataFrame) -> pd.DataFrame:
    ensure_storage()
    normalized = normalize_manual_dataframe(df)
    normalized.to_csv(MANUAL_RECORDS_FILE, index=False, encoding="utf-8")
    return normalized


def append_manual_records(df: pd.DataFrame) -> pd.DataFrame:
    current = load_manual_records()
    incoming = normalize_manual_dataframe(df)
    combined = pd.concat([current, incoming], ignore_index=True)
    combined = combined.drop_duplicates().reset_index(drop=True)
    return save_manual_records(combined)


def replace_professor_records(professor_name: str, df: pd.DataFrame) -> pd.DataFrame:
    current = load_manual_records()
    remaining = current[current["UTN Researcher (s)"] != professor_name].copy()
    replacement = normalize_manual_dataframe(df)
    combined = pd.concat([remaining, replacement], ignore_index=True)
    combined = combined.drop_duplicates().reset_index(drop=True)
    return save_manual_records(combined)


def delete_professor_records(professor_name: str) -> pd.DataFrame:
    current = load_manual_records()
    updated = current[current["UTN Researcher (s)"] != professor_name].copy()
    return save_manual_records(updated) if not updated.empty else _clear_manual_records()


def save_generated_report(report_bytes: bytes, filename: str) -> Path:
    ensure_storage()
    safe_name = filename.replace(" ", "_")
    target = GENERATED_REPORTS_DIR / safe_name
    target.write_bytes(report_bytes)
    return target


def list_generated_reports() -> List[Path]:
    ensure_storage()
    return sorted(GENERATED_REPORTS_DIR.glob("*.xlsx"), key=lambda path: path.stat().st_mtime, reverse=True)


def _clear_manual_records() -> pd.DataFrame:
    empty_df = pd.DataFrame(columns=MANUAL_COLUMNS)
    empty_df.to_csv(MANUAL_RECORDS_FILE, index=False, encoding="utf-8")
    return empty_df
