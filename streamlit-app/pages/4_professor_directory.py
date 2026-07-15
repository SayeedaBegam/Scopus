"""
Professor Directory page - Overview of all professors and their collaborations.
"""

import streamlit as st
import pandas as pd


def show_professor_directory():
    """Display professor directory with collaboration summary."""
    
    if not st.session_state.get('data_loaded'):
        st.error("❌ No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    processor = st.session_state.processor
    df = st.session_state.processed_df
    
    st.markdown("## 👥 Professor Directory")
    
    st.markdown("""
    Overview of all professors and their international collaborations.
    Click on a professor to view detailed information.
    """)
    
    st.markdown("---")
    
    # Get professors and their stats
    professors = processor.get_professors()
    
    if not professors:
        st.warning("No professors found in the data.")
        return
    
    st.markdown(f"### All Professors ({len(professors)})")
    
    # Create a summary table
    professor_stats = []
    
    for prof in professors:
        prof_data = processor.get_professor_data(prof)
        
        # Calculate stats
        num_collaborations = len(prof_data)
        num_countries = prof_data['Country'].nunique()
        num_institutions = prof_data['International Partner Institution'].nunique()
        top_country = prof_data['Country'].value_counts().index[0] if len(prof_data) > 0 else "N/A"
        years = prof_data['Year'].unique()
        year_range = f"{int(min(pd.to_numeric(prof_data['Year'], errors='coerce').dropna())):d}-{int(max(pd.to_numeric(prof_data['Year'], errors='coerce').dropna())):d}" if len(years) > 0 else "N/A"
        
        professor_stats.append({
            'Professor': prof,
            'Collaborations': num_collaborations,
            'Countries': num_countries,
            'Institutions': num_institutions,
            'Top Country': top_country,
            'Year Range': year_range
        })
    
    # Display as table
    stats_df = pd.DataFrame(professor_stats).sort_values('Collaborations', ascending=False)
    
    # Display with columns
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Professor Name**")
    with col2:
        st.markdown("**Collaborations**")
    with col3:
        st.markdown("**Countries**")
    
    st.markdown("---")
    
    for idx, row in stats_df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button(
                f"👤 {row['Professor']}",
                key=f"prof_{idx}",
                use_container_width=True
            ):
                st.session_state.selected_professor = row['Professor']
                st.session_state.current_page = "Professor Profile"
                st.rerun()
        
        with col2:
            st.metric("Collab.", row['Collaborations'], label_visibility="collapsed")
        
        with col3:
            st.metric("Countries", row['Countries'], label_visibility="collapsed")
        
        with col4:
            st.metric("Orgs", row['Institutions'], label_visibility="collapsed")
    
    st.markdown("---")
    
    # Summary statistics
    st.markdown("### 📊 Overall Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Professors", len(professors))
    
    with col2:
        st.metric("Total Collaborations", len(df))
    
    with col3:
        st.metric("Avg per Professor", round(len(df) / len(professors), 1))
    
    with col4:
        st.metric("Total Countries", df['Country'].nunique())
    
    st.markdown("---")
    
    # Top countries and institutions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗺️ Top Partner Countries")
        top_countries = df['Country'].value_counts().head(10)
        for country, count in top_countries.items():
            st.markdown(f"- **{country}**: {count} collaborations")
    
    with col2:
        st.markdown("### 🏫 Top Partner Institutions")
        top_institutions = df['International Partner Institution'].value_counts().head(10)
        for inst, count in top_institutions.items():
            # Truncate long names
            display_inst = inst if len(inst) <= 50 else inst[:47] + "..."
            st.markdown(f"- **{display_inst}**: {count}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
    
    with col2:
        if st.button("📤 Upload New Data", use_container_width=True):
            st.session_state.current_page = "Upload"
            st.rerun()
    
    with col3:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.data_loaded = False
            st.rerun()


if __name__ == "__main__":
    show_professor_directory()
