"""
Country and institution detection utilities for international collaboration analysis.
"""

import re
from typing import Tuple, List, Dict, Optional

# Comprehensive list of countries and their variations
COUNTRIES_MAP = {
    # European countries
    'Germany': ['Germany', 'Deutschland', 'german'],
    'Austria': ['Austria', 'Österreich', 'austrian'],
    'Switzerland': ['Switzerland', 'Schweiz', 'Swiss'],
    'France': ['France', 'French', 'Français'],
    'Italy': ['Italy', 'Italia', 'Italian'],
    'Spain': ['Spain', 'España', 'Spanish'],
    'United Kingdom': ['United Kingdom', 'UK', 'England', 'Scotland', 'Wales', 'British'],
    'Netherlands': ['Netherlands', 'Holland', 'Dutch'],
    'Belgium': ['Belgium', 'Belgian'],
    'Denmark': ['Denmark', 'Danish'],
    'Sweden': ['Sweden', 'Swedish'],
    'Norway': ['Norway', 'Norwegian'],
    'Finland': ['Finland', 'Finnish'],
    'Poland': ['Poland', 'Polish'],
    'Czech Republic': ['Czech Republic', 'Czechia', 'Czech'],
    'Hungary': ['Hungary', 'Hungarian'],
    'Romania': ['Romania', 'Romanian'],
    'Greece': ['Greece', 'Greek'],
    'Portugal': ['Portugal', 'Portuguese'],
    'Ireland': ['Ireland', 'Irish'],
    
    # Americas
    'United States': ['United States', 'USA', 'U.S.A.', 'US', 'U.S.', 'America'],
    'Canada': ['Canada', 'Canadian'],
    'Mexico': ['Mexico', 'Mexican'],
    'Brazil': ['Brazil', 'Brazilian'],
    'Argentina': ['Argentina', 'Argentine', 'Argentinian'],
    'Chile': ['Chile', 'Chilean'],
    'Colombia': ['Colombia', 'Colombian'],
    'Peru': ['Peru', 'Peruvian'],
    
    # Asia
    'China': ['China', 'Chinese', 'P.R. China', 'Mainland China'],
    'Japan': ['Japan', 'Japanese'],
    'South Korea': ['South Korea', 'Korea', 'Republic of Korea'],
    'India': ['India', 'Indian'],
    'Thailand': ['Thailand', 'Thai'],
    'Vietnam': ['Vietnam', 'Vietnamese'],
    'Singapore': ['Singapore', 'Singaporean'],
    'Malaysia': ['Malaysia', 'Malaysian'],
    'Indonesia': ['Indonesia', 'Indonesian'],
    'Taiwan': ['Taiwan', 'Chinese Taipei'],
    'Hong Kong': ['Hong Kong', 'HK'],
    'Pakistan': ['Pakistan', 'Pakistani'],
    'Bangladesh': ['Bangladesh', 'Bangladeshi'],
    'Philippines': ['Philippines', 'Philippine'],
    'Thailand': ['Thailand', 'Thai'],
    'Iran': ['Iran', 'Iranian'],
    'Israel': ['Israel', 'Israeli'],
    'Saudi Arabia': ['Saudi Arabia', 'Saudi'],
    'UAE': ['United Arab Emirates', 'UAE', 'U.A.E.'],
    'Turkey': ['Turkey', 'Turkish'],
    
    # Oceania
    'Australia': ['Australia', 'Australian'],
    'New Zealand': ['New Zealand', 'Aotearoa', 'NZ'],
    
    # Africa
    'South Africa': ['South Africa', 'South African'],
    'Egypt': ['Egypt', 'Egyptian'],
    'Nigeria': ['Nigeria', 'Nigerian'],
    'Kenya': ['Kenya', 'Kenyan'],
    'Ethiopia': ['Ethiopia', 'Ethiopian'],
}

# Build reverse map for faster lookup
COUNTRY_REVERSE_MAP = {}
for country, variations in COUNTRIES_MAP.items():
    for variation in variations:
        COUNTRY_REVERSE_MAP[variation.lower()] = country

# Common German institution keywords
GERMAN_KEYWORDS = [
    'university', 'universität', 'technische', 'tu', 'hochschule',
    'institute', 'institut', 'school', 'college', 'max-planck',
    'fraunhofer', 'helmholtz', 'research', 'zentrum', 'centre'
]


def detect_country(affiliation_text: str) -> Tuple[Optional[str], bool]:
    """
    Detect country from affiliation text.
    
    Args:
        affiliation_text: Full affiliation string
        
    Returns:
        Tuple of (country_name, is_uncertain)
        is_uncertain = True if detection confidence is low
    """
    if not affiliation_text or not isinstance(affiliation_text, str):
        return None, True
    
    text = affiliation_text.strip()
    
    # Extract the last part (usually country)
    # Affiliations often format as: "Institution, City, Country"
    parts = [p.strip() for p in text.split(',')]
    
    # Check last part first (most likely to be country)
    if len(parts) > 0:
        last_part = parts[-1]
        country = COUNTRY_REVERSE_MAP.get(last_part.lower())
        if country:
            return country, False
    
    # Check all parts
    for part in parts:
        part_clean = part.lower().strip()
        country = COUNTRY_REVERSE_MAP.get(part_clean)
        if country:
            return country, False
    
    # Try pattern matching for variations
    text_lower = text.lower()
    for variation, country in COUNTRY_REVERSE_MAP.items():
        if variation.lower() in text_lower:
            # Higher uncertainty for partial matches
            return country, len(variation) < 3
    
    return None, True


def is_german_institution(institution_text: str) -> bool:
    """Check if institution is German-based."""
    if not institution_text or not isinstance(institution_text, str):
        return False
    
    text = institution_text.lower()
    
    # Check for explicit German country indicators
    if 'germany' in text or 'deutschland' in text or 'german' in text:
        return True
    
    # Common German city/region indicators
    german_indicators = [
        'münchen', 'munich',
        'berlin',
        'hamburg',
        'cologne', 'köln',
        'frankfurt',
        'heidelberg',
        'bonn',
        'mainz',
        'heidelberg',
        'darmstadt',
        'karlsruhe',
        'düsseldorf',
        'dresden',
        'göttingen',
        'würzburg',
        'erlangen',
        'bochum',
        'essen',
        'tübingen',
        'freiburg',
        'mannheim',
        'hamburg'
    ]
    
    for indicator in german_indicators:
        if indicator in text:
            return True
    
    return False


def extract_institutions(affiliation_text: str) -> List[str]:
    """
    Extract individual institutions from affiliation text.
    
    Affiliations often contain multiple institutions separated by semicolons or other delimiters.
    """
    if not affiliation_text or not isinstance(affiliation_text, str):
        return []
    
    # Split by common delimiters
    text = affiliation_text.replace(';', '|').replace('\n', '|')
    institutions = [inst.strip() for inst in text.split('|') if inst.strip()]
    
    return institutions


def process_affiliations(affiliations_text: str) -> List[Dict[str, any]]:
    """
    Process raw affiliations string into structured data.
    
    Args:
        affiliations_text: Raw affiliations from Scopus CSV
        
    Returns:
        List of dicts with: institution, country, is_german, needs_review
    """
    if not affiliations_text or not isinstance(affiliations_text, str):
        return []
    
    institutions = extract_institutions(affiliations_text)
    results = []
    
    for institution in institutions:
        # Skip if empty after strip
        if not institution:
            continue
        
        # Check if German
        is_german = is_german_institution(institution)
        
        # Detect country
        country, is_uncertain = detect_country(institution)
        
        # Build result
        result = {
            'institution': institution,
            'country': country,
            'is_german': is_german,
            'needs_review': is_uncertain or (country is None and not is_german)
        }
        
        results.append(result)
    
    return results


def filter_international_affiliations(affiliations_data: List[Dict]) -> List[Dict]:
    """Filter out German affiliations, keeping only international ones."""
    return [aff for aff in affiliations_data if not aff['is_german']]


def get_confidence_level(institution_data: Dict) -> str:
    """Return confidence level for institution detection."""
    if institution_data.get('needs_review'):
        return 'Low'
    return 'High'
