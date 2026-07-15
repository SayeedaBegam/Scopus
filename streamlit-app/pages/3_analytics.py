"""
Analytics and overview page.
"""

import streamlit as st
import pandas as pd
from utils.ui_utils import (
    create_collaborations_by_country_chart,
    create_collaborations_by_year_chart,
    create_top_institutions_chart,
    create_professor_collaboration_chart,
    format_dataframe_for_display,
    get_statistics_cards_data
)


def show_analytics_page():
    """Display analytics and overview."""
    
    if not st.session_state.get('data_loaded'):
        st.error("❌ No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    processor = st.session_state.processor
    df = st.session_state.processed_df
    
    st.markdown("## 📊 Analytics & Overview")
    
    # Statistics cards
    st.markdown("### Key Statistics")
    
    stats = processor.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📈 Total Publications",
            stats['total_publications'],
            help="Number of publications analyzed"
        )
    
    with col2:
        st.metric(
            "🌍 International Rows",
            stats['total_collaborations'],
            help="Number of international collaborations identified"
        )
    
    with col3:
        st.metric(
            "🗺️ Countries",
            stats['num_countries'],
            help="Number of unique partner countries"
        )
    
    with col4:
        st.metric(
            "🏫 Institutions",
            stats['num_institutions'],
            help="Number of unique partner institutions"
        )
    
    st.markdown("---")
    
    # Charts
    st.markdown("### 📈 Visualizations")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "By Country",
        "Over Time",
        "Top Institutions",
        "By Professor"
    ])
    
    with tab1:
        fig = create_collaborations_by_country_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for chart")
    
    with tab2:
        fig = create_collaborations_by_year_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid year data for chart")
    
    with tab3:
        fig = create_top_institutions_chart(df, limit=12)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for chart")
    
    with tab4:
        fig = create_professor_collaboration_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for chart")
    
    st.markdown("---")
    
    # Detailed data table
    st.markdown("### 📋 All Collaboration Data")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        professors = ["All Professors"] + processor.get_professors()
        selected_professor = st.selectbox(
            "Filter by Professor",
            professors,
            index=0
        )
    
    with col2:
        countries = sorted(df['Country'].unique().tolist())
        selected_country = st.multiselect(
            "Filter by Country",
            countries,
            default=[]
        )
    
    with col3:
        needs_review = st.checkbox("Show only 'Needs Review' items", value=False)
    
    # Apply filters
    filtered_df = processor.get_professor_data(selected_professor)
    
    if selected_country:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_country)]
    
    if needs_review:
        filtered_df = filtered_df[filtered_df['Needs Review'] == 'Yes']
    
    # Show filtered data
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} rows**")
    
    display_df = format_dataframe_for_display(filtered_df)
    st.dataframe(display_df, use_container_width=True)
    
    # Export option
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    
    if st.button("Download as CSV", use_container_width=True):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Click here to download",
            data=csv,
            file_name="international_collaborations.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👥 View Professor Details", use_container_width=True):
            st.session_state.current_page = "Professor Directory"
            st.rerun()
    
    with col2:
        if st.button("📤 Upload New Data", use_container_width=True):
            st.session_state.current_page = "Upload"
            st.rerun()


if __name__ == "__main__":
    show_analytics_page()
