"""
Manual CSV processing utilities for cleaned collaboration exports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd


MANUAL_COLUMNS = [
    "Year",
    "No of Author(s)",
    "Source Title",
    "Publication Title",
    "UTN Researcher (s)",
    "UTN Department(s)",
    "UTN Lab",
    "Other University Researcher(s)",
    "Other University/Institution",
    "Other University Department/Lab",
    "Country",
]

REQUIRED_MANUAL_COLUMNS = [
    "Year",
    "Source Title",
    "Publication Title",
    "UTN Researcher (s)",
    "Other University/Institution",
    "Country",
]


def load_manual_csv(csv_file) -> Tuple[bool, str, pd.DataFrame]:
    """Load a cleaned manual CSV file."""
    try:
        df = pd.read_csv(csv_file, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_file, encoding="latin-1")
        except Exception as exc:
            return False, f"Error loading CSV: {exc}", pd.DataFrame()
    except Exception as exc:
        return False, f"Error loading CSV: {exc}", pd.DataFrame()

    try:
        normalized = normalize_manual_dataframe(df)
    except ValueError as exc:
        return False, str(exc), pd.DataFrame()

    return True, f"Loaded {len(normalized)} manual collaboration rows", normalized


def normalize_manual_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize the manual CSV schema."""
    if df is None:
        raise ValueError("No CSV data found.")

    normalized = df.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]

    missing_required = [column for column in REQUIRED_MANUAL_COLUMNS if column not in normalized.columns]
    if missing_required:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_required)
            + ". Expected columns include: "
            + ", ".join(MANUAL_COLUMNS)
        )

    for column in MANUAL_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[MANUAL_COLUMNS].copy()
    normalized = normalized.fillna("")

    for column in MANUAL_COLUMNS:
        normalized[column] = normalized[column].astype(str).str.strip()

    normalized = normalized[normalized["UTN Researcher (s)"] != ""].reset_index(drop=True)

    return normalized


def manual_to_processed_df(df: pd.DataFrame) -> pd.DataFrame:
    """Map a manual CSV dataframe into the dashboard's analytics schema."""
    normalized = normalize_manual_dataframe(df)

    processed = pd.DataFrame(
        {
            "Professor Name": normalized["UTN Researcher (s)"],
            "Year": normalized["Year"],
            "Publication Title": normalized["Publication Title"],
            "Source Title": normalized["Source Title"],
            "Authors": normalized["Other University Researcher(s)"],
            "International Partner Institution": normalized["Other University/Institution"],
            "Partner Department/Lab": normalized["Other University Department/Lab"],
            "Country": normalized["Country"],
            "DOI": "",
            "Needs Review": "No",
            "Notes": normalized.apply(_build_notes_column, axis=1),
        }
    )

    return processed.fillna("")


def get_manual_professors(df: pd.DataFrame) -> List[str]:
    """Return sorted professor names from a manual dataframe."""
    normalized = normalize_manual_dataframe(df)
    return sorted(name for name in normalized["UTN Researcher (s)"].unique().tolist() if name)


def summarize_manual_dataframe(df: pd.DataFrame) -> Dict[str, int]:
    """Compute simple summary metrics for a manual dataframe."""
    normalized = normalize_manual_dataframe(df)
    return {
        "rows": len(normalized),
        "professors": normalized["UTN Researcher (s)"].nunique(),
        "countries": normalized["Country"].nunique(),
        "institutions": normalized["Other University/Institution"].nunique(),
    }


def _build_notes_column(row: pd.Series) -> str:
    note_parts = []
    if row.get("UTN Department(s)", ""):
        note_parts.append(f"UTN Department: {row['UTN Department(s)']}")
    if row.get("UTN Lab", ""):
        note_parts.append(f"UTN Lab: {row['UTN Lab']}")
    return " | ".join(note_parts)


@dataclass
class StoredCollaborationProcessor:
    """Adapter that exposes the same interface as the Scopus processor."""

    processed_df: pd.DataFrame

    def get_processed_df(self) -> pd.DataFrame:
        return self.processed_df.copy()

    def get_professors(self) -> List[str]:
        if self.processed_df.empty:
            return []
        return sorted(self.processed_df["Professor Name"].dropna().astype(str).unique().tolist())

    def get_professor_data(self, professor_name: str) -> pd.DataFrame:
        if professor_name == "All Professors":
            return self.processed_df.copy()
        return self.processed_df[self.processed_df["Professor Name"] == professor_name].copy()

    def get_statistics(self, df: Optional[pd.DataFrame] = None) -> Dict[str, int]:
        data = self.processed_df if df is None else df
        if data is None or data.empty:
            return {
                "total_publications": 0,
                "total_collaborations": 0,
                "num_countries": 0,
                "num_institutions": 0,
                "num_professors": 0,
            }

        return {
            "total_publications": len(data),
            "total_collaborations": len(data),
            "num_countries": data["Country"].nunique(),
            "num_institutions": data["International Partner Institution"].nunique(),
            "num_professors": data["Professor Name"].nunique(),
        }
