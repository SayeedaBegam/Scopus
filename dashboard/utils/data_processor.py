"""
Data processing utilities for Scopus CSV exports.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

import pandas as pd

from utils.country_detector import detect_country, is_german_institution
from utils.manual_processor import manual_to_processed_df, normalize_manual_dataframe


class ScopusCSVProcessor:
    """Process Scopus CSV exports and generate international collaboration data."""
    
    # Possible column name variations from different Scopus exports
    COLUMN_MAPPINGS = {
        'authors': ['Authors', 'Author(s)', 'authors'],
        'title': ['Title', 'Document Title', 'title', 'article title'],
        'year': ['Year', 'year', 'publication year', 'year published'],
        'source': ['Source Title', 'source title', 'Journal', 'journal', 'Conference Name'],
        'authors_with_affiliations': ['Authors with affiliations', 'authors with affiliations'],
        'author_full_names': ['Author full names', 'author full names'],
        'affiliations': ['Affiliations', 'affiliations', 'author affiliations'],
        'doi': ['DOI', 'doi'],
        'abstract': ['Abstract', 'abstract'],
        'keywords': ['Keywords', 'keywords'],
        'document_type': ['Document Type', 'document type', 'type'],
    }
    
    def __init__(self, csv_file=None):
        """Initialize processor, optionally with CSV file."""
        self.raw_df = None
        self.processed_df = None
        self.reporting_df = None
        self.utn_researcher = ""
        self.utn_department = ""
        self.utn_lab = ""
        if csv_file is not None:
            self.load_csv(csv_file)
    
    def load_csv(self, csv_file) -> Tuple[bool, str]:
        """
        Load and validate CSV file.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.raw_df = pd.read_csv(csv_file, encoding='utf-8', dtype={'Year': str})
            return True, f"Successfully loaded {len(self.raw_df)} publications"
        except UnicodeDecodeError:
            try:
                self.raw_df = pd.read_csv(csv_file, encoding='latin-1', dtype={'Year': str})
                return True, f"Successfully loaded {len(self.raw_df)} publications (using latin-1 encoding)"
            except Exception as e:
                return False, f"Error loading CSV: {str(e)}"
        except Exception as e:
            return False, f"Error loading CSV: {str(e)}"
    
    def find_column(self, standard_name: str) -> Optional[str]:
        """Find actual column name from possible variations."""
        if self.raw_df is None:
            return None
        
        possible_names = self.COLUMN_MAPPINGS.get(standard_name.lower(), [standard_name])
        
        for possible_name in possible_names:
            for actual_column in self.raw_df.columns:
                if actual_column.lower() == possible_name.lower():
                    return actual_column
        
        return None
    
    def get_available_columns(self) -> List[str]:
        """Return list of available columns in loaded CSV."""
        if self.raw_df is None:
            return []
        return self.raw_df.columns.tolist()
    
    def process(self) -> Tuple[bool, str]:
        """
        Process loaded CSV into the UTN reporting structure.
        Creates one row per publication and international partner group.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.raw_df is None:
            return False, "No CSV loaded"
        
        try:
            # Find columns
            authors_col = self.find_column('authors')
            title_col = self.find_column('title')
            year_col = self.find_column('year')
            source_col = self.find_column('source')
            author_full_names_col = self.find_column('author_full_names')
            authors_with_affiliations_col = self.find_column('authors_with_affiliations')
            affiliations_col = self.find_column('affiliations')
            doi_col = self.find_column('doi')
            
            if not affiliations_col or not authors_with_affiliations_col:
                return False, (
                    "Cannot find the required Scopus affiliation columns. "
                    "Available columns: " + ", ".join(self.raw_df.columns)
                )

            self.utn_researcher = self._infer_target_researcher(authors_col, author_full_names_col)
            self.utn_lab, self.utn_department = self._infer_utn_context(
                authors_with_affiliations_col,
                affiliations_col,
                authors_col,
            )
            
            # Process each publication
            processed_rows = []
            
            for _, row in self.raw_df.iterrows():
                affiliations_text = row.get(affiliations_col, '')
                authors_with_affiliations = row.get(authors_with_affiliations_col, '')
                authors_text = row.get(authors_col, '')
                
                if not affiliations_text or (isinstance(affiliations_text, float) and pd.isna(affiliations_text)):
                    continue

                report_rows = self._build_reporting_rows(
                    row=row,
                    authors_text=str(authors_text),
                    authors_with_affiliations=str(authors_with_affiliations),
                    affiliations_text=str(affiliations_text),
                    year_col=year_col,
                    title_col=title_col,
                    source_col=source_col,
                )
                processed_rows.extend(report_rows)

            if not processed_rows:
                self.reporting_df = pd.DataFrame()
                self.processed_df = pd.DataFrame()
                return False, "No international collaborations found in the data"

            self.reporting_df = normalize_manual_dataframe(pd.DataFrame(processed_rows))
            self.processed_df = manual_to_processed_df(self.reporting_df)
            
            return True, (
                f"Successfully processed {len(self.reporting_df)} reporting rows "
                f"from {len(self.raw_df)} publications"
            )
        
        except Exception as e:
            return False, f"Error processing CSV: {str(e)}"
    
    @staticmethod
    def _extract_first_author(authors_str: str) -> str:
        """Extract first author name from authors string."""
        if not authors_str or (isinstance(authors_str, float) and pd.isna(authors_str)):
            return "Unknown"
        
        # Usually separated by comma or semicolon
        first = str(authors_str).split(',')[0].split(';')[0].strip()
        return first if first else "Unknown"
    
    def get_processed_df(self) -> Optional[pd.DataFrame]:
        """Return analytics dataframe."""
        return self.processed_df

    def get_reporting_df(self) -> Optional[pd.DataFrame]:
        """Return UTN reporting dataframe."""
        return self.reporting_df
    
    def get_professors(self) -> List[str]:
        """Get list of unique professors from processed data."""
        if self.processed_df is None:
            return []
        return sorted(self.processed_df['Professor Name'].unique().tolist())
    
    def get_professor_data(self, professor_name: str) -> pd.DataFrame:
        """Get all data for a specific professor."""
        if self.processed_df is None:
            return pd.DataFrame()
        
        if professor_name == "All Professors":
            return self.processed_df.copy()
        
        return self.processed_df[self.processed_df['Professor Name'] == professor_name].copy()
    
    def get_statistics(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """Calculate statistics from processed data."""
        data = df if df is not None else self.processed_df
        
        if data is None or len(data) == 0:
            return {
                'total_publications': 0,
                'total_collaborations': 0,
                'num_countries': 0,
                'num_institutions': 0,
            }
        
        return {
            'total_publications': len(data),
            'total_collaborations': len(data),
            'num_countries': data['Country'].nunique(),
            'num_institutions': data['International Partner Institution'].nunique(),
            'num_professors': data['Professor Name'].nunique(),
        }
    
    def export_csv(self, professor_name: Optional[str] = None) -> Tuple[str, pd.DataFrame]:
        """Export processed data as CSV."""
        if professor_name and professor_name != "All Professors":
            df = self.get_professor_data(professor_name)
            filename = f"collaborations_{professor_name.replace(' ', '_')}.csv"
        else:
            df = self.processed_df
            filename = "all_collaborations.csv"
        
        return filename, df

    def _infer_target_researcher(self, authors_col: Optional[str], author_full_names_col: Optional[str]) -> str:
        """Infer the UTN researcher from the most frequent author in the export."""
        if self.raw_df is None or not authors_col:
            return "UTN Researcher"

        author_counter: Counter = Counter()
        for authors_text in self.raw_df[authors_col].fillna("").astype(str):
            author_counter.update(self._split_authors(authors_text))

        if not author_counter:
            return "UTN Researcher"

        target_short = author_counter.most_common(1)[0][0]
        if not author_full_names_col:
            return target_short

        for full_names_text in self.raw_df[author_full_names_col].fillna("").astype(str):
            for entry in self._split_scopus_full_names(full_names_text):
                if self._short_name_from_full_entry(entry) == target_short:
                    return self._display_name_from_full_entry(entry)

        return target_short

    def _infer_utn_context(
        self,
        authors_with_affiliations_col: str,
        affiliations_col: str,
        authors_col: Optional[str],
    ) -> Tuple[str, str]:
        """Infer the current UTN lab and department heuristically."""
        target_short = ""
        if authors_col and self.raw_df is not None:
            counter = Counter()
            for authors_text in self.raw_df[authors_col].fillna("").astype(str):
                counter.update(self._split_authors(authors_text))
            if counter:
                target_short = counter.most_common(1)[0][0]

        candidate_affiliations: List[str] = []
        for _, row in self.raw_df.iterrows():
            chunks = self._split_author_affiliation_chunks(str(row.get(authors_with_affiliations_col, "")))
            for author_name, affiliation_text in chunks:
                if author_name == target_short:
                    candidate_affiliations.extend(self._split_affiliation_list(affiliation_text))

        best_affiliation = ""
        priority_keywords = ["nuremberg", "fundamental ai lab", "technology nuremberg", "funai lab"]
        for affiliation in candidate_affiliations:
            if any(keyword in affiliation.lower() for keyword in priority_keywords):
                best_affiliation = affiliation
                break

        if not best_affiliation and candidate_affiliations:
            best_affiliation = candidate_affiliations[0]

        lab = self._extract_department_or_lab(best_affiliation)
        department = self._map_lab_to_department(lab)
        return lab, department

    def _build_reporting_rows(
        self,
        row: pd.Series,
        authors_text: str,
        authors_with_affiliations: str,
        affiliations_text: str,
        year_col: Optional[str],
        title_col: Optional[str],
        source_col: Optional[str],
    ) -> List[Dict[str, str]]:
        """Convert a Scopus row to the manual UTN reporting structure."""
        author_list = self._split_authors(authors_text)
        author_chunks = self._split_author_affiliation_chunks(authors_with_affiliations)
        target_short = self._find_target_short_name(author_list)
        affiliation_groups: Dict[Tuple[str, str, str], List[str]] = {}

        for affiliation in self._split_affiliation_list(affiliations_text):
            if not affiliation:
                continue

            country, _ = detect_country(affiliation)
            if not country:
                country = self._guess_country_from_affiliation(affiliation)
            if country == "Germany" or is_german_institution(affiliation):
                continue

            institution = self._extract_institution_name(affiliation)
            department = self._extract_department_or_lab(affiliation)
            key = (institution, department, country or "Unknown")
            matched_authors = []

            for author_name, author_affiliation_text in author_chunks:
                if author_name == target_short:
                    continue
                if affiliation in author_affiliation_text:
                    matched_authors.append(author_name)

            if matched_authors:
                existing = affiliation_groups.setdefault(key, [])
                for author_name in matched_authors:
                    if author_name not in existing:
                        existing.append(author_name)

        rows = []
        for (institution, department, country), collaborators in affiliation_groups.items():
            rows.append(
                {
                    "Year": self._clean_year(row.get(year_col, "")),
                    "No of Author(s)": str(len(author_list)),
                    "Source Title": str(row.get(source_col, "")).strip(),
                    "Publication Title": str(row.get(title_col, "")).strip(),
                    "UTN Researcher (s)": self.utn_researcher,
                    "UTN Department(s)": self.utn_department,
                    "UTN Lab": self.utn_lab,
                    "Other University Researcher(s)": "; ".join(collaborators),
                    "Other University/Institution": institution,
                    "Other University Department/Lab": department,
                    "Country": country,
                }
            )

        return rows

    @staticmethod
    def _split_authors(authors_text: str) -> List[str]:
        return [author.strip() for author in str(authors_text).split(";") if author.strip()]

    @staticmethod
    def _split_scopus_full_names(full_names_text: str) -> List[str]:
        return [entry.strip() for entry in str(full_names_text).split(";") if entry.strip()]

    @staticmethod
    def _short_name_from_full_entry(entry: str) -> str:
        name_part = entry.split("(")[0].strip()
        if "," not in name_part:
            return name_part
        surname, given_names = [part.strip() for part in name_part.split(",", 1)]
        initials = "".join(
            f"{token[0]}."
            for token in given_names.split()
            if token and token[0].isalpha()
        )
        return f"{surname} {initials}".strip()

    @staticmethod
    def _display_name_from_full_entry(entry: str) -> str:
        name_part = entry.split("(")[0].strip()
        if "," not in name_part:
            return name_part
        surname, given_names = [part.strip() for part in name_part.split(",", 1)]
        given_tokens = [token for token in given_names.split() if len(token.replace(".", "")) > 1]
        display_given = " ".join(given_tokens) if given_tokens else given_names.split()[0]
        return f"{display_given} {surname}".strip()

    @staticmethod
    def _split_author_affiliation_chunks(authors_with_affiliations: str) -> List[Tuple[str, str]]:
        chunks = []
        for chunk in str(authors_with_affiliations).split(";"):
            chunk = chunk.strip()
            if not chunk or "," not in chunk:
                continue
            author_name, affiliation_text = chunk.split(",", 1)
            chunks.append((author_name.strip(), affiliation_text.strip()))
        return chunks

    @staticmethod
    def _split_affiliation_list(affiliations_text: str) -> List[str]:
        return [aff.strip() for aff in str(affiliations_text).split(";") if aff.strip()]

    def _find_target_short_name(self, author_list: List[str]) -> str:
        if not author_list:
            return ""
        for author in author_list:
            if self._normalize_name(author) == self._normalize_name(self.utn_researcher):
                return author
        for author in author_list:
            if self.utn_researcher and author.split()[0].lower() in self.utn_researcher.lower():
                return author
        return author_list[-1]

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-z]", "", str(name).lower())

    @staticmethod
    def _extract_institution_name(affiliation: str) -> str:
        parts = [part.strip() for part in affiliation.split(",") if part.strip()]
        if not parts:
            return affiliation.strip()
        if len(parts) >= 2:
            return parts[1] if ScopusCSVProcessor._looks_like_department(parts[0]) else parts[0]
        return parts[0]

    @staticmethod
    def _extract_department_or_lab(affiliation: str) -> str:
        parts = [part.strip() for part in affiliation.split(",") if part.strip()]
        if len(parts) <= 1:
            return ""
        return parts[0] if ScopusCSVProcessor._looks_like_department(parts[0]) else ""

    @staticmethod
    def _looks_like_department(part: str) -> bool:
        tokens = ["department", "lab", "laboratory", "centre", "center", "school", "faculty", "institute", "group"]
        return any(token in part.lower() for token in tokens)

    @staticmethod
    def _map_lab_to_department(lab: str) -> str:
        lab_key = lab.lower().strip()
        mappings = {
            "fundamental ai lab": "CSAI",
            "funai lab": "CSAI",
        }
        return mappings.get(lab_key, "")

    @staticmethod
    def _guess_country_from_affiliation(affiliation: str) -> str:
        parts = [part.strip() for part in affiliation.split(",") if part.strip()]
        return parts[-1] if parts else "Unknown"

    @staticmethod
    def _clean_year(year_value) -> str:
        if pd.isna(year_value):
            return ""
        year_text = str(year_value).strip()
        return year_text[:-2] if year_text.endswith(".0") else year_text
