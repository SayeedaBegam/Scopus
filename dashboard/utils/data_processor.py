"""
Data processing utilities for Scopus CSV exports.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict
from utils.country_detector import process_affiliations, filter_international_affiliations


class ScopusCSVProcessor:
    """Process Scopus CSV exports and generate international collaboration data."""
    
    # Possible column name variations from different Scopus exports
    COLUMN_MAPPINGS = {
        'authors': ['Authors', 'Author(s)', 'authors'],
        'title': ['Title', 'Document Title', 'title', 'article title'],
        'year': ['Year', 'year', 'publication year', 'year published'],
        'source': ['Source Title', 'source title', 'Journal', 'journal', 'Conference Name'],
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
        Process loaded CSV into international collaboration data.
        Creates one row per international partner institution.
        
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
            affiliations_col = self.find_column('affiliations')
            doi_col = self.find_column('doi')
            
            if not affiliations_col:
                return False, "Cannot find 'Affiliations' column. Available columns: " + ", ".join(self.raw_df.columns)
            
            # Process each publication
            processed_rows = []
            
            for idx, row in self.raw_df.iterrows():
                affiliations_text = row.get(affiliations_col, '')
                
                if not affiliations_text or (isinstance(affiliations_text, float) and pd.isna(affiliations_text)):
                    continue
                
                # Parse affiliations
                affiliations_data = process_affiliations(str(affiliations_text))
                international_affs = filter_international_affiliations(affiliations_data)
                
                # If no international collaborations, skip
                if not international_affs:
                    continue
                
                # Create one row per international affiliation
                for aff in international_affs:
                    processed_row = {
                        'Professor Name': self._extract_first_author(row.get(authors_col, '')),
                        'Year': row.get(year_col, ''),
                        'Publication Title': row.get(title_col, ''),
                        'Source Title': row.get(source_col, ''),
                        'Authors': row.get(authors_col, ''),
                        'International Partner Institution': aff['institution'],
                        'Partner Department/Lab': '',  # To be filled manually
                        'Country': aff['country'] or 'Unknown',
                        'DOI': row.get(doi_col, ''),
                        'Needs Review': 'Yes' if aff['needs_review'] else 'No',
                        'Notes': '',
                    }
                    processed_rows.append(processed_row)
            
            self.processed_df = pd.DataFrame(processed_rows)
            
            if len(self.processed_df) == 0:
                return False, "No international collaborations found in the data"
            
            return True, f"Successfully processed {len(self.processed_df)} international collaboration rows from {len(self.raw_df)} publications"
        
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
        """Return processed dataframe."""
        return self.processed_df
    
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
