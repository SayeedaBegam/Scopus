"""
UTN International Joint Publications Dashboard
Main Streamlit application entry point.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure page
st.set_page_config(
    page_title="UTN International Collaborations",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'processor' not in st.session_state:
    st.session_state.processor = None

if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

if 'selected_professor' not in st.session_state:
    st.session_state.selected_professor = None


# Show theme customization in sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("## 🎨 Dashboard Settings")
    
    theme = st.radio(
        "Color Theme",
        ["Light", "Dark"],
        label_visibility="collapsed",
        horizontal=True
    )


# Import page display functions from utils
from utils.data_processor import ScopusCSVProcessor
from utils.manual_processor import (
    MANUAL_COLUMNS,
    StoredCollaborationProcessor,
    get_manual_professors,
    load_manual_csv,
    manual_to_processed_df,
    normalize_manual_dataframe,
    summarize_manual_dataframe,
)
from utils.storage import (
    append_manual_records,
    delete_professor_records,
    list_generated_reports,
    load_manual_records,
    replace_professor_records,
    save_generated_report,
)
from utils.ui_utils import (
    create_collaborations_by_country_chart,
    create_collaborations_by_year_chart,
    create_top_institutions_chart,
    create_professor_collaboration_chart,
    format_dataframe_for_display
)
from utils.excel_exporter import create_manual_tracking_excel, create_professional_excel_export
import pandas as pd


def show_upload_page():
    """Display CSV upload interface."""
    st.markdown("## 📤 Upload Publication Data")
    
    st.markdown("""
    Upload a Scopus CSV export containing publication information and author affiliations.
    The system will automatically extract international collaborations.
    """)
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file from Scopus export",
        type="csv",
        help="Download from Scopus: Menu → Export → CSV (All fields)"
    )
    
    if uploaded_file is not None:
        st.markdown("---")
        
        with st.spinner("Processing your file..."):
            processor = ScopusCSVProcessor()
            
            success, message = processor.load_csv(uploaded_file)
            
            if success:
                st.success(message)
                
                with st.expander("📋 Detected columns in your CSV"):
                    columns = processor.get_available_columns()
                    st.write(f"Total columns detected: {len(columns)}")
                    cols_display = ", ".join(columns)
                    st.caption(cols_display)
                
                with st.expander("👁️ Preview of raw data"):
                    st.dataframe(processor.raw_df.head(5), use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Processing Data")
                
                process_success, process_message = processor.process()
                
                if process_success:
                    st.success(f"✅ {process_message}")
                    
                    st.session_state.processor = processor
                    st.session_state.processed_df = processor.get_processed_df()
                    st.session_state.data_loaded = True
                    
                    st.markdown("### 📊 Processing Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    stats = processor.get_statistics()
                    
                    with col1:
                        st.metric("Total Publications", stats['total_publications'])
                    with col2:
                        st.metric("International Rows", stats['total_collaborations'])
                    with col3:
                        st.metric("Countries", stats['num_countries'])
                    with col4:
                        st.metric("Institutions", stats['num_institutions'])
                    
                    st.markdown("---")
                    
                    with st.expander("👁️ Preview of processed international collaborations"):
                        preview_df = processor.get_processed_df().head(10)
                        st.dataframe(preview_df, use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("### ✨ Next Steps")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📊 View Analytics", use_container_width=True):
                            st.session_state.current_page = "Analytics"
                            st.rerun()
                    
                    with col2:
                        if st.button("👥 View Professors", use_container_width=True):
                            st.session_state.current_page = "Professor Directory"
                            st.rerun()
                    
                    with col3:
                        if st.button("🔄 Upload New File", use_container_width=True):
                            st.session_state.data_loaded = False
                            st.session_state.processor = None
                            st.rerun()
                
                else:
                    st.error(f"❌ {process_message}")
                    
                    st.markdown("### ⚠️ Troubleshooting")
                    
                    st.markdown("""
                    The system could not find international collaborations. This might be because:
                    
                    1. **Missing Affiliations column** - Your CSV may not include author affiliations
                       - Make sure to export with "All fields" option from Scopus
                    
                    2. **No international collaborations** - All partnerships might be domestic (Germany-only)
                    
                    3. **Column format issue** - Column names might be different
                       - The system looks for: Authors, Title, Year, Source Title, Affiliations, DOI
                    """)
                    
                    if st.button("Try Another File"):
                        st.rerun()
            
            else:
                st.error(f"❌ {message}")
                st.markdown("""
                ### 📝 Supported Format
                
                Export CSV from Scopus with these steps:
                1. Go to Scopus and search for publications
                2. Select publications
                3. Click "Export" → "Export all" 
                4. Choose "CSV" format
                5. Check "All fields" option
                6. Click "Export"
                """)
    
    else:
        st.markdown("### 📝 How to Export from Scopus")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Step-by-step:**
            
            1. Go to [www.scopus.com](https://www.scopus.com)
            2. Search for author (e.g., your professor's name)
            3. Click "Documents" in left panel
            4. Select all relevant publications
            5. Click "Export all" button
            6. Choose "CSV (All fields)"
            7. Save the file
            """)
        
        with col2:
            st.markdown("""
            **CSV Should Contain:**
            
            - ✓ Authors
            - ✓ Document Title
            - ✓ Year
            - ✓ Source Title
            - ✓ **Affiliations** (most important!)
            - ✓ DOI
            
            **Note:** This prototype only supports CSV uploads. Scopus API integration coming later.
            """)


def show_manual_workflow_page():
    """Display the manual cleaned-CSV to Excel workflow."""
    st.markdown("## Manual CSV to Excel")
    st.markdown(
        """
        Use this page when the collaboration data has already been prepared in a cleaned CSV.
        Upload the CSV, preview it, save the professor records locally, and generate the final Excel sheet.
        """
    )

    st.info(
        "Expected CSV columns: "
        + ", ".join(MANUAL_COLUMNS)
    )

    tab1, tab2 = st.tabs(["Upload Manual CSV", "Saved Excel Reports"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload the cleaned collaboration CSV",
            type="csv",
            key="manual_csv_upload",
            help="This is the manual export that already follows the international joint publications template.",
        )

        if uploaded_file is not None:
            success, message, manual_df = load_manual_csv(uploaded_file)
            if not success:
                st.error(f"❌ {message}")
                return

            st.success(message)
            stats = summarize_manual_dataframe(manual_df)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rows", stats["rows"])
            with col2:
                st.metric("Professors", stats["professors"])
            with col3:
                st.metric("Countries", stats["countries"])
            with col4:
                st.metric("Institutions", stats["institutions"])

            st.markdown("### Preview")
            st.dataframe(manual_df, use_container_width=True)

            professors = get_manual_professors(manual_df)
            if professors:
                st.caption("Detected professors: " + ", ".join(professors))

            st.markdown("### Actions")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Save Records to Library", use_container_width=True):
                    combined = append_manual_records(manual_df)
                    st.success(f"Saved records. Library now contains {len(combined)} rows.")

            with col2:
                if st.button("Load into Analytics", use_container_width=True):
                    processed_df = manual_to_processed_df(manual_df)
                    st.session_state.processor = StoredCollaborationProcessor(processed_df)
                    st.session_state.processed_df = processed_df
                    st.session_state.data_loaded = True
                    st.session_state.current_page = "Analytics"
                    st.rerun()

            with col3:
                if st.button("Generate and Save Excel", use_container_width=True):
                    excel_bytes = create_manual_tracking_excel(manual_df)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_path = save_generated_report(excel_bytes, f"international_joint_publications_{timestamp}.xlsx")
                    st.success(f"Saved Excel report to {report_path.name}")
                    st.download_button(
                        label="Download Saved Excel",
                        data=excel_bytes,
                        file_name=report_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
        else:
            st.markdown("### Workflow")
            st.markdown(
                """
                1. Prepare or export the cleaned CSV using the international joint publications columns.
                2. Upload it here.
                3. Save the professor rows to the dashboard library if you want them stored locally.
                4. Generate the Excel report and keep the saved copy inside the dashboard data folder.
                """
            )

    with tab2:
        reports = list_generated_reports()
        if not reports:
            st.info("No saved Excel reports yet.")
        else:
            st.markdown(f"### Saved Reports ({len(reports)})")
            for index, report_path in enumerate(reports, start=1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    modified = datetime.fromtimestamp(report_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    st.markdown(f"**{index}. {report_path.name}**")
                    st.caption(f"Updated {modified}")
                with col2:
                    st.download_button(
                        label="Download",
                        data=report_path.read_bytes(),
                        file_name=report_path.name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"saved_report_{report_path.name}",
                        use_container_width=True,
                    )


def show_professor_library_page():
    """Display saved professor records and allow local management."""
    st.markdown("## Stored Professors")
    st.markdown(
        """
        This page manages the professor records saved from the manual CSV workflow.
        You can review rows, update them, add new rows, load them into analytics, or delete a professor entirely.
        """
    )

    records_df = load_manual_records()
    if records_df.empty:
        st.info("No professor records have been stored yet.")
    else:
        professors = get_manual_professors(records_df)
        selected_professor = st.selectbox("Choose a stored professor", professors, key="stored_professor_select")
        professor_df = records_df[records_df["UTN Researcher (s)"] == selected_professor].reset_index(drop=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(professor_df))
        with col2:
            st.metric("Countries", professor_df["Country"].nunique())
        with col3:
            st.metric("Institutions", professor_df["Other University/Institution"].nunique())

        st.markdown("### Edit Professor Records")
        edited_df = st.data_editor(
            professor_df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{selected_professor}",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Changes", use_container_width=True):
                try:
                    edited_df = normalize_manual_dataframe(edited_df)
                    replace_professor_records(selected_professor, edited_df)
                    st.success(f"Saved updated records for {selected_professor}.")
                    st.rerun()
                except ValueError as exc:
                    st.error(f"❌ {exc}")

        with col2:
            if st.button("Load into Analytics", use_container_width=True, key=f"load_{selected_professor}"):
                processed_df = manual_to_processed_df(edited_df)
                st.session_state.processor = StoredCollaborationProcessor(processed_df)
                st.session_state.processed_df = processed_df
                st.session_state.data_loaded = True
                st.session_state.selected_professor = selected_professor
                st.session_state.current_page = "Professor Profile"
                st.rerun()

        with col3:
            if st.button("Delete Professor", use_container_width=True, key=f"delete_{selected_professor}"):
                delete_professor_records(selected_professor)
                st.success(f"Deleted all stored records for {selected_professor}.")
                st.rerun()

    st.markdown("---")
    st.markdown("### Add a Manual Record")

    with st.form("add_manual_record_form"):
        col1, col2 = st.columns(2)
        with col1:
            professor_name = st.text_input("UTN Researcher (s)")
            year = st.text_input("Year")
            source_title = st.text_input("Source Title")
            publication_title = st.text_input("Publication Title")
            country = st.text_input("Country")
            no_of_authors = st.text_input("No of Author(s)")
        with col2:
            utn_department = st.text_input("UTN Department(s)")
            utn_lab = st.text_input("UTN Lab")
            other_researchers = st.text_input("Other University Researcher(s)")
            other_institution = st.text_input("Other University/Institution")
            other_department = st.text_input("Other University Department/Lab")

        submitted = st.form_submit_button("Add Record", use_container_width=True)

        if submitted:
            new_row = pd.DataFrame(
                [
                    {
                        "Year": year,
                        "No of Author(s)": no_of_authors,
                        "Source Title": source_title,
                        "Publication Title": publication_title,
                        "UTN Researcher (s)": professor_name,
                        "UTN Department(s)": utn_department,
                        "UTN Lab": utn_lab,
                        "Other University Researcher(s)": other_researchers,
                        "Other University/Institution": other_institution,
                        "Other University Department/Lab": other_department,
                        "Country": country,
                    }
                ]
            )
            try:
                append_manual_records(new_row)
                st.success(f"Added record for {professor_name}.")
                st.rerun()
            except ValueError as exc:
                st.error(f"❌ {exc}")


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
    
    st.markdown("### Key Statistics")
    
    stats = processor.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Total Publications", stats['total_publications'])
    with col2:
        st.metric("🌍 International Rows", stats['total_collaborations'])
    with col3:
        st.metric("🗺️ Countries", stats['num_countries'])
    with col4:
        st.metric("🏫 Institutions", stats['num_institutions'])
    
    st.markdown("---")
    
    st.markdown("### 📈 Visualizations")
    
    tab1, tab2, tab3, tab4 = st.tabs(["By Country", "Over Time", "Top Institutions", "By Professor"])
    
    with tab1:
        fig = create_collaborations_by_country_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = create_collaborations_by_year_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = create_top_institutions_chart(df, limit=12)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        fig = create_professor_collaboration_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📋 All Collaboration Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        professors = ["All Professors"] + processor.get_professors()
        selected_professor = st.selectbox("Filter by Professor", professors, index=0)
    
    with col2:
        countries = sorted(df['Country'].unique().tolist())
        selected_country = st.multiselect("Filter by Country", countries, default=[])
    
    with col3:
        needs_review = st.checkbox("Show only 'Needs Review' items", value=False)
    
    filtered_df = processor.get_professor_data(selected_professor)
    
    if selected_country:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_country)]
    
    if needs_review:
        filtered_df = filtered_df[filtered_df['Needs Review'] == 'Yes']
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} rows**")
    
    display_df = format_dataframe_for_display(filtered_df)
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download as Excel (Professional)", use_container_width=True, key="excel_prof"):
            excel_data = create_professional_excel_export(filtered_df)
            st.download_button(
                label="📥 Download Professional Excel",
                data=excel_data,
                file_name="international_collaborations.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        if st.button("📄 Download as CSV", use_container_width=True):
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
    
    st.markdown("Overview of all professors and their international collaborations.")
    
    st.markdown("---")
    
    professors = processor.get_professors()
    
    if not professors:
        st.warning("No professors found in the data.")
        return
    
    st.markdown(f"### All Professors ({len(professors)})")
    
    professor_stats = []
    
    for prof in professors:
        prof_data = processor.get_professor_data(prof)
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
    
    stats_df = pd.DataFrame(professor_stats).sort_values('Collaborations', ascending=False)
    
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
            if st.button(f"👤 {row['Professor']}", key=f"prof_{idx}", use_container_width=True):
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗺️ Top Partner Countries")
        top_countries = df['Country'].value_counts().head(10)
        for country, count in top_countries.items():
            st.markdown(f"- **{country}**: {count}")
    
    with col2:
        st.markdown("### 🏫 Top Partner Institutions")
        top_institutions = df['International Partner Institution'].value_counts().head(10)
        for inst, count in top_institutions.items():
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


def show_professor_profile():
    """Display detailed professor profile."""
    
    if not st.session_state.get('data_loaded'):
        st.error("❌ No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    processor = st.session_state.processor
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
        st.markdown("### 🗺️ Countries")
        countries = prof_data['Country'].value_counts()
        for country, count in countries.items():
            st.markdown(f"- **{country}**: {count}")
    
    st.markdown("---")
    st.markdown("### 📋 All Collaborations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        countries = sorted(prof_data['Country'].unique().tolist())
        selected_countries = st.multiselect("Filter by Country", countries, default=countries[:3] if len(countries) > 0 else [])
    
    with col2:
        needs_review_filter = st.checkbox("Show only 'Needs Review'", value=False)
    
    filtered_df = prof_data[prof_data['Country'].isin(selected_countries)] if selected_countries else prof_data
    
    if needs_review_filter:
        filtered_df = filtered_df[filtered_df['Needs Review'] == 'Yes']
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(prof_data)} rows**")
    
    display_df = format_dataframe_for_display(filtered_df)
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    
    if st.session_state.get('user_role') == 'Admin':
        st.markdown("### ✏️ Admin: Edit Data")
        
        with st.expander("📝 Edit Table Rows"):
            st.markdown("This feature allows you to edit the collaboration data directly.")
            st.info("**Planned features:** Edit institution names, update countries, add notes, mark as reviewed")
        
        with st.expander("🗑️ Delete Rows"):
            st.markdown("Select rows to delete (coming in next phase)")
    
    else:
        st.markdown("### 🔒 Data Access")
        if st.button("📥 Request Download Access", use_container_width=True):
            st.success("✅ **Download Request Submitted** - An administrator will review within 1-2 business days.")
    
    st.markdown("---")
    
    st.markdown("### 💾 Export Professor Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download as Excel", use_container_width=True, key="export_prof_excel"):
            excel_data = create_professional_excel_export(filtered_df, selected_professor)
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"collaborations_{selected_professor.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col2:
        if st.button("📄 Download as CSV", use_container_width=True, key="export_prof_csv"):
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


def show_login_page():
    """Display login/role selector page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🎓 UTN International Collaboration Dashboard")
        st.markdown("### Welcome!")
        st.markdown("---")
        
        st.markdown("#### Select Your Role")
        role = st.radio(
            "Choose your role:",
            ["Admin", "Viewer"],
            horizontal=False,
            help="Admin: Full access to upload, edit, and export data. Viewer: View-only access."
        )
        
        st.session_state.user_role = role
        
        st.markdown("---")
        
        st.markdown("""
        ### About This Dashboard
        
        This dashboard helps track **international collaboration** between UTN (Universität für 
        Technologie Niederösterreich) and partner institutions worldwide.
        
        **Features:**
        - 📤 Upload Scopus publication exports
        - 🏫 View international partner institutions and countries
        - 👨‍🔬 Track collaboration by professor
        - 📊 Analyze collaboration trends and statistics
        - 💾 Export collaboration data
        
        #### How it works:
        1. Export publications from Scopus as CSV
        2. Upload the CSV file
        3. View and explore international collaborations
        4. Export cleaned data for further analysis
        
        ---
        """)
        
        if role == "Admin":
            st.success("✅ Admin Mode: You have full editing and export capabilities.")
            st.markdown("""
            **Your Admin Capabilities:**
            - Edit collaboration details
            - Delete erroneous entries
            - Export data as CSV
            - Manage professor information
            """)
        else:
            st.info("ℹ️ Viewer Mode: You can view all data but cannot make edits.")
            st.markdown("""
            **Your Viewer Capabilities:**
            - View all collaborations and statistics
            - Search and filter data
            - Download visualizations
            - Request download access for data
            """)
        
        st.markdown("---")
        
        if st.button("🚀 Continue to Dashboard", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.session_state.current_page = "Upload"
            st.rerun()
        
        st.markdown("""
        ---
        **Data Privacy Notice:** All data is processed locally in your browser session.
        No data is permanently stored on external servers.
        """)


def show_main_content():
    """Route to the appropriate page based on authentication and current page."""
    
    # Show home/login if not authenticated
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Sidebar navigation after login
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_role}")
        st.markdown("---")
        
        st.markdown("### Navigation")
        
        # Navigation buttons
        if st.button("📤 Upload Data", use_container_width=True):
            st.session_state.current_page = "Upload"
            st.rerun()

        if st.button("🧾 Manual CSV to Excel", use_container_width=True):
            st.session_state.current_page = "Manual Workflow"
            st.rerun()

        if st.button("🗂️ Stored Professors", use_container_width=True):
            st.session_state.current_page = "Stored Professors"
            st.rerun()
        
        if st.session_state.data_loaded:
            if st.button("📊 Analytics", use_container_width=True):
                st.session_state.current_page = "Analytics"
                st.rerun()
            
            if st.button("👥 Professor Directory", use_container_width=True):
                st.session_state.current_page = "Professor Directory"
                st.rerun()
            
            if st.session_state.current_page == "Professor Profile" and st.session_state.selected_professor:
                st.markdown(f"#### Current Professor")
                st.markdown(f"**{st.session_state.selected_professor}**")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.data_loaded = False
            st.session_state.processor = None
            st.session_state.processed_df = None
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        ### ℹ️ Help
        
        **Upload CSV:** Export publications from Scopus as CSV with all fields
        
        **Manual CSV to Excel:** Upload the cleaned collaboration CSV and save the generated Excel locally
        
        **Stored Professors:** Review, edit, add, or delete saved professor records
        
        **Process Data:** System automatically detects international collaborations
        
        **View Details:** Browse by professor or view overall analytics
        
        **Export:** Download processed data for further analysis
        """)
        
        st.markdown("---")
        if st.session_state.get('user_role') == 'Admin':
            st.success("✅ Admin Mode Active")
        else:
            st.info("👁️ Viewer Mode Active")
    
    # Route to current page
    if st.session_state.current_page == "Upload":
        show_upload_page()

    elif st.session_state.current_page == "Manual Workflow":
        show_manual_workflow_page()

    elif st.session_state.current_page == "Stored Professors":
        show_professor_library_page()
    
    elif st.session_state.current_page == "Analytics":
        show_analytics_page()
    
    elif st.session_state.current_page == "Professor Directory":
        show_professor_directory()
    
    elif st.session_state.current_page == "Professor Profile":
        show_professor_profile()
    
    else:
        # Default to upload
        show_upload_page()


# Main app
st.markdown("""
<style>
.stMetric {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

show_main_content()
