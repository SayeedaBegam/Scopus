"""
UI and charting utilities.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List


def create_collaborations_by_country_chart(df: pd.DataFrame):
    """Create bar chart of collaborations by country."""
    if df is None or len(df) == 0:
        return None
    
    country_counts = df['Country'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Collaborations']
    country_counts = country_counts.sort_values('Collaborations', ascending=False)
    
    fig = px.bar(
        country_counts.head(15),
        x='Country',
        y='Collaborations',
        title='International Collaborations by Country',
        color='Collaborations',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        xaxis_title='Country',
        yaxis_title='Number of Collaborations',
        height=400,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def create_collaborations_by_year_chart(df: pd.DataFrame):
    """Create line chart of collaborations by year."""
    if df is None or len(df) == 0:
        return None
    
    # Convert year to numeric, handle errors
    df_copy = df.copy()
    df_copy['Year'] = pd.to_numeric(df_copy['Year'], errors='coerce')
    df_copy = df_copy.dropna(subset=['Year'])
    
    if len(df_copy) == 0:
        return None
    
    year_counts = df_copy.groupby('Year').size().reset_index(name='Collaborations')
    year_counts = year_counts.sort_values('Year')
    
    fig = px.line(
        year_counts,
        x='Year',
        y='Collaborations',
        title='Collaborations Over Time',
        markers=True,
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Number of Collaborations',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_top_institutions_chart(df: pd.DataFrame, limit: int = 10):
    """Create bar chart of top partner institutions."""
    if df is None or len(df) == 0:
        return None
    
    inst_counts = df['International Partner Institution'].value_counts().reset_index()
    inst_counts.columns = ['Institution', 'Collaborations']
    
    fig = px.bar(
        inst_counts.head(limit),
        x='Collaborations',
        y='Institution',
        title=f'Top {limit} Partner Institutions',
        orientation='h',
        color='Collaborations',
        color_continuous_scale='Plasma'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig


def create_professor_collaboration_chart(df: pd.DataFrame):
    """Create chart showing collaborations per professor."""
    if df is None or len(df) == 0:
        return None
    
    prof_counts = df['Professor Name'].value_counts().reset_index()
    prof_counts.columns = ['Professor', 'Collaborations']
    prof_counts = prof_counts.sort_values('Collaborations', ascending=False)
    
    fig = px.bar(
        prof_counts,
        x='Professor',
        y='Collaborations',
        title='Collaborations by Professor',
        color='Collaborations',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title='Professor',
        yaxis_title='Number of Collaborations'
    )
    
    return fig


def format_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Format dataframe for nice display in Streamlit."""
    display_df = df.copy()
    
    # Truncate long text for readability
    for col in display_df.columns:
        if display_df[col].dtype == 'object':
            display_df[col] = display_df[col].astype(str).apply(
                lambda x: x if len(x) <= 100 else x[:97] + '...'
            )
    
    return display_df


def get_statistics_cards_data(stats: Dict) -> Dict:
    """Prepare statistics for card display."""
    return {
        'Total Publications': stats.get('total_publications', 0),
        'International Collaborations': stats.get('total_collaborations', 0),
        'Partner Countries': stats.get('num_countries', 0),
        'Partner Institutions': stats.get('num_institutions', 0),
    }
