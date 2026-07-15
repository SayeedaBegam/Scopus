"""
Professor Profile page - Detailed view of a professor's collaborations.
"""

import streamlit as st
import pandas as pd
from utils.ui_utils import (
    create_collaborations_by_country_chart,
    create_collaborations_by_year_chart,
    create_top_institutions_chart,
    format_dataframe_for_display
)


def show_professor_profile():
    """Display detailed professor profile."""
    
    if not st.session_state.get('data_loaded'):
        st.error("❌ No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    processor = st.session_state.processor
    
    # Get selected professor
    selected_professor = st.session_state.get('selected_professor')
    
    if not selected_professor:
        st.error("No professor selected.")
        if st.button("Back to Directory"):
            st.session_state.current_page = "Professor Directory"
            st.rerun()
        return
    
    prof_data = processor.get_professor_data(selected_professor)
    
    if len(prof_data) == 0:
        st.error(f"No data found for professor: {selected_professor}")
        if st.button("Back to Directory"):
            st.session_state.current_page = "Professor Directory"
            st.rerun()
        return
    
    # Header with professor info
    st.markdown(f"## 👤 {selected_professor}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("International Collaborations", len(prof_data))
    
    with col2:
        st.metric("Partner Countries", prof_data['Country'].nunique())
    
    with col3:
        st.metric("Partner Institutions", prof_data['International Partner Institution'].nunique())
    
    with col4:
        years = pd.to_numeric(prof_data['Year'], errors='coerce').dropna()
        if len(years) > 0:
            st.metric("Years Active", f"{int(min(years))}-{int(max(years))}")
        else:
            st.metric("Years Active", "N/A")
    
    st.markdown("---")
    
    # Charts
    st.markdown("### 📈 Collaboration Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_collaborations_by_country_chart(prof_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = create_collaborations_by_year_chart(prof_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_top_institutions_chart(prof_data, limit=10)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Country breakdown
        st.markdown("### 🗺️ Countries")
        countries = prof_data['Country'].value_counts()
        
        for country, count in countries.items():
            st.markdown(f"- **{country}**: {count} collaboration(s)")
    
    st.markdown("---")
    
    # Detailed data table with editing capabilities
    st.markdown("### 📋 All Collaborations")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        countries = sorted(prof_data['Country'].unique().tolist())
        selected_countries = st.multiselect(
            "Filter by Country",
            countries,
            default=countries[:3] if len(countries) > 0 else []
        )
    
    with col2:
        needs_review_filter = st.checkbox("Show only 'Needs Review'", value=False)
    
    # Apply filters
    filtered_df = prof_data[prof_data['Country'].isin(selected_countries)] if selected_countries else prof_data
    
    if needs_review_filter:
        filtered_df = filtered_df[filtered_df['Needs Review'] == 'Yes']
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(prof_data)} rows**")
    
    # Display data table
    display_df = format_dataframe_for_display(filtered_df)
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    
    # Admin editing features
    if st.session_state.get('user_role') == 'Admin':
        st.markdown("### ✏️ Admin: Edit Data")
        
        with st.expander("📝 Edit Table Rows"):
            st.markdown("""
            This feature allows you to edit the collaboration data directly.
            (Full editing UI coming in next phase)
            """)
            
            st.info("""
            **Planned features:**
            - Edit institution names and details
            - Update country assignments
            - Add/remove notes
            - Mark items as reviewed
            """)
        
        with st.expander("🗑️ Delete Rows"):
            st.markdown("Select rows to delete (coming in next phase)")
    
    else:
        st.markdown("### 🔒 Data Access")
        
        if st.button("📥 Request Download Access", use_container_width=True):
            st.success("""
            ✅ **Download Request Submitted**
            
            Your request has been recorded. An administrator will review your request 
            and provide access to download this data within 1-2 business days.
            """)
    
    st.markdown("---")
    
    # Export data
    st.markdown("### 💾 Export Professor Data")
    
    if st.button("Download as CSV", use_container_width=True, key="export_prof"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Click here to download",
            data=csv,
            file_name=f"collaborations_{selected_professor.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Back to Directory", use_container_width=True):
            st.session_state.current_page = "Professor Directory"
            st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
    
    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.data_loaded = False
            st.rerun()


if __name__ == "__main__":
    show_professor_profile()
