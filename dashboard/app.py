"""
UTN International Joint Publications Dashboard
Main Streamlit application entry point.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_processor import ScopusCSVProcessor
from utils.excel_exporter import create_manual_tracking_excel, create_professional_excel_export
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
    create_professor_collaboration_chart,
    create_top_institutions_chart,
    format_dataframe_for_display,
)


st.set_page_config(
    page_title="UTN International Collaborations",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "processor" not in st.session_state:
    st.session_state.processor = None

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "selected_professor" not in st.session_state:
    st.session_state.selected_professor = None


with st.sidebar:
    st.markdown("---")
    st.markdown("## Dashboard Settings")
    st.radio(
        "Theme mode",
        ["Light"],
        index=0,
        disabled=True,
        label_visibility="collapsed",
        horizontal=True,
    )


def render_page_header(title: str, intro: str, eyebrow: str = "UTN Dashboard") -> None:
    """Render a consistent page header."""
    st.markdown(
        f"""
        <section class="hero-panel">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{intro}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_info_cards(items) -> None:
    """Render compact informational cards."""
    cards = "".join(
        f"""
        <div class="info-card">
            <div class="info-card-title">{title}</div>
            <div class="info-card-body">{body}</div>
        </div>
        """
        for title, body in items
    )
    st.markdown(f'<div class="info-card-grid">{cards}</div>', unsafe_allow_html=True)


def show_upload_page():
    """Display CSV upload interface."""
    render_page_header(
        "Upload Publication Data",
        "Upload a Scopus CSV export with affiliations. The dashboard validates the file, extracts international collaboration rows, and prepares them for analytics and export.",
        "Automated Workflow",
    )
    render_info_cards(
        [
            ("Required Export", "Use Scopus CSV export with all fields so the affiliations column is included."),
            ("What Happens Next", "The system filters to international partners and creates one collaboration row per partner institution."),
            ("Best Use Case", "Use this workflow when starting from raw Scopus output rather than a manually prepared reporting sheet."),
        ]
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV file from Scopus export",
        type="csv",
        help="Download from Scopus: Menu -> Export -> CSV (All fields)",
    )

    if uploaded_file is not None:
        st.markdown("---")

        with st.spinner("Processing your file..."):
            processor = ScopusCSVProcessor()
            success, message = processor.load_csv(uploaded_file)

            if success:
                st.success(message)

                with st.expander("Detected columns in your CSV"):
                    columns = processor.get_available_columns()
                    st.write(f"Total columns detected: {len(columns)}")
                    st.caption(", ".join(columns))

                with st.expander("Preview of raw data"):
                    st.dataframe(processor.raw_df.head(5), use_container_width=True)

                st.markdown("---")
                st.markdown("### Processing Data")

                process_success, process_message = processor.process()

                if process_success:
                    st.success(process_message)

                    st.session_state.processor = processor
                    st.session_state.processed_df = processor.get_processed_df()
                    st.session_state.data_loaded = True

                    st.markdown("### Processing Summary")
                    stats = processor.get_statistics()

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Publications", stats["total_publications"])
                    with col2:
                        st.metric("International Rows", stats["total_collaborations"])
                    with col3:
                        st.metric("Countries", stats["num_countries"])
                    with col4:
                        st.metric("Institutions", stats["num_institutions"])

                    st.markdown("---")
                    with st.expander("Preview of processed international collaborations"):
                        st.dataframe(processor.get_processed_df().head(10), use_container_width=True)

                    st.markdown("---")
                    st.markdown("### Next Steps")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("View Analytics", use_container_width=True):
                            st.session_state.current_page = "Analytics"
                            st.rerun()
                    with col2:
                        if st.button("View Professors", use_container_width=True):
                            st.session_state.current_page = "Professor Directory"
                            st.rerun()
                    with col3:
                        if st.button("Upload New File", use_container_width=True):
                            st.session_state.data_loaded = False
                            st.session_state.processor = None
                            st.rerun()
                else:
                    st.error(process_message)
                    st.markdown("### Troubleshooting")
                    st.markdown(
                        """
                        The system could not find international collaborations. This might be because:

                        1. **Missing Affiliations column**
                           Make sure to export with the "All fields" option from Scopus.
                        2. **No international collaborations**
                           All partnerships might be domestic only.
                        3. **Column format issue**
                           The system looks for Authors, Title, Year, Source Title, Affiliations, and DOI.
                        """
                    )
                    if st.button("Try Another File"):
                        st.rerun()
            else:
                st.error(message)
                st.markdown(
                    """
                    ### Supported Format

                    Export CSV from Scopus with these steps:
                    1. Go to Scopus and search for publications.
                    2. Select publications.
                    3. Click "Export" then "Export all".
                    4. Choose CSV format.
                    5. Check "All fields".
                    6. Download the file.
                    """
                )
    else:
        st.markdown("### Export Guidance")
        col1, col2 = st.columns([1.15, 1], gap="large")

        with col1:
            st.markdown(
                """
                **Step-by-step**

                1. Go to [www.scopus.com](https://www.scopus.com)
                2. Search for the UTN researcher
                3. Open the documents list
                4. Select the relevant publications
                5. Choose "Export all"
                6. Select "CSV (All fields)"
                7. Save the file and upload it here
                """
            )

        with col2:
            st.markdown(
                """
                **CSV should contain**

                - Authors
                - Document Title
                - Year
                - Source Title
                - Affiliations
                - DOI

                The affiliations column is required to identify international collaborations.
                """
            )


def show_manual_workflow_page():
    """Display the manual cleaned-CSV to Excel workflow."""
    render_page_header(
        "Manual CSV to Excel",
        "Use this page when the collaboration data has already been curated in the UTN joint-publications format. Upload the file, review the rows, and produce the final Excel output.",
        "Manual Workflow",
    )

    st.info("Expected CSV columns: " + ", ".join(MANUAL_COLUMNS))
    render_info_cards(
        [
            ("Input Format", "The uploaded file should already match the manual collaboration template used for UTN reporting."),
            ("Excel Output", "The generated workbook keeps the reporting structure and summary sections required for later review."),
            ("Stored Library", "You can save uploaded records locally so they appear again in the stored professors workspace."),
        ]
    )

    tab1, tab2 = st.tabs(["Upload Manual CSV", "Saved Excel Reports"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload the cleaned collaboration CSV",
            type="csv",
            key="manual_csv_upload",
            help="This file should already follow the international joint publications template.",
        )

        if uploaded_file is not None:
            success, message, manual_df = load_manual_csv(uploaded_file)
            if not success:
                st.error(message)
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
                    report_path = save_generated_report(
                        excel_bytes,
                        f"international_joint_publications_{timestamp}.xlsx",
                    )
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
                3. Save the professor rows to the local library if you want them available later.
                4. Generate the Excel report and keep the saved copy in the dashboard data folder.
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
    render_page_header(
        "Stored Professors",
        "Manage the locally saved professor records from the manual workflow. Review saved rows, edit them, add missing entries, or load a professor back into analytics.",
        "Record Library",
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
                    st.error(str(exc))

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
                st.error(str(exc))


def show_analytics_page():
    """Display analytics and overview."""
    if not st.session_state.get("data_loaded"):
        st.error("No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return

    processor = st.session_state.processor
    df = st.session_state.processed_df

    render_page_header(
        "Analytics and Overview",
        "Review the processed collaboration dataset through summary statistics, time trends, country distribution, institution rankings, and professor-level breakdowns.",
        "Analytics",
    )

    st.markdown("### Key Statistics")
    stats = processor.get_statistics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Publications", stats["total_publications"])
    with col2:
        st.metric("International Rows", stats["total_collaborations"])
    with col3:
        st.metric("Countries", stats["num_countries"])
    with col4:
        st.metric("Institutions", stats["num_institutions"])

    st.markdown("---")
    st.markdown("### Visualizations")

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
    st.markdown("### All Collaboration Data")

    col1, col2, col3 = st.columns(3)
    with col1:
        professors = ["All Professors"] + processor.get_professors()
        selected_professor = st.selectbox("Filter by Professor", professors, index=0)
    with col2:
        countries = sorted(df["Country"].unique().tolist())
        selected_country = st.multiselect("Filter by Country", countries, default=[])
    with col3:
        needs_review = st.checkbox("Show only 'Needs Review' items", value=False)

    filtered_df = processor.get_professor_data(selected_professor)
    if selected_country:
        filtered_df = filtered_df[filtered_df["Country"].isin(selected_country)]
    if needs_review:
        filtered_df = filtered_df[filtered_df["Needs Review"] == "Yes"]

    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} rows**")
    st.dataframe(format_dataframe_for_display(filtered_df), use_container_width=True)

    st.markdown("---")
    st.markdown("### Export Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download as Excel", use_container_width=True, key="excel_prof"):
            excel_data = create_professional_excel_export(filtered_df)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="international_collaborations.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with col2:
        if st.button("Download as CSV", use_container_width=True):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="international_collaborations.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("View Professor Details", use_container_width=True):
            st.session_state.current_page = "Professor Directory"
            st.rerun()
    with col2:
        if st.button("Upload New Data", use_container_width=True):
            st.session_state.current_page = "Upload"
            st.rerun()


def show_professor_directory():
    """Display professor directory with collaboration summary."""
    if not st.session_state.get("data_loaded"):
        st.error("No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return

    processor = st.session_state.processor
    df = st.session_state.processed_df

    render_page_header(
        "Professor Directory",
        "Browse all professors detected in the current dataset and compare their collaboration volume, partner countries, and institutions.",
        "Directory",
    )

    professors = processor.get_professors()
    if not professors:
        st.warning("No professors found in the data.")
        return

    professor_stats = []
    for prof in professors:
        prof_data = processor.get_professor_data(prof)
        years = pd.to_numeric(prof_data["Year"], errors="coerce").dropna()
        if len(years) > 0:
            year_range = f"{int(min(years))}-{int(max(years))}"
        else:
            year_range = "N/A"

        professor_stats.append(
            {
                "Professor": prof,
                "Collaborations": len(prof_data),
                "Countries": prof_data["Country"].nunique(),
                "Institutions": prof_data["International Partner Institution"].nunique(),
                "Top Country": prof_data["Country"].value_counts().index[0] if len(prof_data) > 0 else "N/A",
                "Year Range": year_range,
            }
        )

    stats_df = pd.DataFrame(professor_stats).sort_values("Collaborations", ascending=False)

    st.markdown(f"### All Professors ({len(professors)})")
    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    st.markdown("### Open a Professor Profile")
    selected_professor = st.selectbox("Select professor", stats_df["Professor"].tolist())
    if st.button("Open Professor Profile", use_container_width=True):
        st.session_state.selected_professor = selected_professor
        st.session_state.current_page = "Professor Profile"
        st.rerun()

    st.markdown("---")
    st.markdown("### Overall Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Professors", len(professors))
    with col2:
        st.metric("Total Collaborations", len(df))
    with col3:
        st.metric("Average per Professor", round(len(df) / len(professors), 1))
    with col4:
        st.metric("Total Countries", df["Country"].nunique())

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Top Partner Countries")
        for country, count in df["Country"].value_counts().head(10).items():
            st.markdown(f"- **{country}**: {count}")
    with col2:
        st.markdown("### Top Partner Institutions")
        for inst, count in df["International Partner Institution"].value_counts().head(10).items():
            display_inst = inst if len(inst) <= 50 else inst[:47] + "..."
            st.markdown(f"- **{display_inst}**: {count}")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
    with col2:
        if st.button("Upload New Data", use_container_width=True):
            st.session_state.current_page = "Upload"
            st.rerun()
    with col3:
        if st.button("Home", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.data_loaded = False
            st.rerun()


def show_professor_profile():
    """Display detailed professor profile."""
    if not st.session_state.get("data_loaded"):
        st.error("No data loaded. Please upload a CSV file first.")
        if st.button("Go to Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return

    processor = st.session_state.processor
    selected_professor = st.session_state.get("selected_professor")

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

    render_page_header(
        selected_professor,
        "Review this professor's collaboration footprint, partner institutions, country spread, and downloadable records.",
        "Professor Profile",
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("International Collaborations", len(prof_data))
    with col2:
        st.metric("Partner Countries", prof_data["Country"].nunique())
    with col3:
        st.metric("Partner Institutions", prof_data["International Partner Institution"].nunique())
    with col4:
        years = pd.to_numeric(prof_data["Year"], errors="coerce").dropna()
        st.metric("Years Active", f"{int(min(years))}-{int(max(years))}" if len(years) > 0 else "N/A")

    st.markdown("---")
    st.markdown("### Collaboration Visualizations")

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
        st.markdown("### Countries")
        for country, count in prof_data["Country"].value_counts().items():
            st.markdown(f"- **{country}**: {count}")

    st.markdown("---")
    st.markdown("### All Collaborations")

    col1, col2 = st.columns(2)
    with col1:
        countries = sorted(prof_data["Country"].unique().tolist())
        selected_countries = st.multiselect(
            "Filter by Country",
            countries,
            default=countries[:3] if len(countries) > 0 else [],
        )
    with col2:
        needs_review_filter = st.checkbox("Show only 'Needs Review'", value=False)

    filtered_df = prof_data[prof_data["Country"].isin(selected_countries)] if selected_countries else prof_data
    if needs_review_filter:
        filtered_df = filtered_df[filtered_df["Needs Review"] == "Yes"]

    st.markdown(f"**Showing {len(filtered_df)} of {len(prof_data)} rows**")
    st.dataframe(format_dataframe_for_display(filtered_df), use_container_width=True)

    st.markdown("---")
    if st.session_state.get("user_role") == "Admin":
        st.markdown("### Admin: Edit Data")
        with st.expander("Edit Table Rows"):
            st.info("Planned enhancement: direct editing of institution names, countries, notes, and review status.")
        with st.expander("Delete Rows"):
            st.write("Planned enhancement: row deletion controls for incorrect collaboration entries.")
    else:
        st.markdown("### Data Access")
        if st.button("Request Download Access", use_container_width=True):
            st.success("Download request submitted. An administrator will review it within 1 to 2 business days.")

    st.markdown("---")
    st.markdown("### Export Professor Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download as Excel", use_container_width=True, key="export_prof_excel"):
            excel_data = create_professional_excel_export(filtered_df, selected_professor)
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name=f"collaborations_{selected_professor.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with col2:
        if st.button("Download as CSV", use_container_width=True, key="export_prof_csv"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"collaborations_{selected_professor.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Back to Directory", use_container_width=True):
            st.session_state.current_page = "Professor Directory"
            st.rerun()
    with col2:
        if st.button("View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
    with col3:
        if st.button("Home", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.data_loaded = False
            st.rerun()


def show_login_page():
    """Display login/role selector page."""
    col1, col2 = st.columns([1.45, 1], gap="large")

    with col1:
        render_page_header(
            "UTN International Collaboration Dashboard",
            "A single workspace for preparing publication exports, converting manual collaboration sheets, reviewing professor activity, and producing reporting-ready Excel files.",
            "Welcome",
        )
        render_info_cards(
            [
                ("Scopus Workflow", "Upload raw Scopus exports with affiliations and turn them into structured collaboration records."),
                ("Manual Workflow", "Upload the curated joint-publications CSV and generate the required Excel sheet directly from the dashboard."),
                ("Professor Review", "Inspect stored records, open professor-specific summaries, and keep the reporting workflow organized."),
            ]
        )
        st.markdown(
            """
            <div class="content-panel">
                <h3>How the dashboard is organized</h3>
                <ul>
                    <li><strong>Upload Data</strong> processes raw Scopus CSV exports with affiliations.</li>
                    <li><strong>Manual CSV to Excel</strong> handles the curated reporting sheet and produces the final Excel output.</li>
                    <li><strong>Stored Professors</strong> keeps locally saved professor records available for later review.</li>
                    <li><strong>Analytics and Professor Directory</strong> help review countries, institutions, and professor-level collaboration patterns.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown('<div class="content-panel">', unsafe_allow_html=True)
        st.markdown("### Select Access Mode")
        role = st.radio(
            "Choose your role:",
            ["Admin", "Viewer"],
            horizontal=False,
            help="Admin: full access to upload, export, and manage local records. Viewer: read-only exploration of the processed data.",
        )
        st.session_state.user_role = role

        if role == "Admin":
            st.success("Admin mode enables upload, export, and local record management.")
            st.markdown(
                """
                **Admin access includes**
                - Uploading Scopus exports
                - Managing manual CSV records
                - Generating Excel deliverables
                - Reviewing professor-level data
                """
            )
        else:
            st.info("Viewer mode focuses on exploration and review.")
            st.markdown(
                """
                **Viewer access includes**
                - Reviewing collaboration summaries
                - Filtering analytics by professor and country
                - Downloading prepared outputs
                - Requesting data exports when needed
                """
            )

        if st.button("Open Dashboard", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.session_state.current_page = "Upload"
            st.rerun()

        st.caption(
            "Data is processed inside the running app session. Long-term hosted storage should use a proper external database or file store."
        )
        st.markdown("</div>", unsafe_allow_html=True)


def show_main_content():
    """Route to the appropriate page based on authentication and current page."""
    if not st.session_state.authenticated:
        show_login_page()
        return

    with st.sidebar:
        st.markdown(f"## {st.session_state.user_role}")
        st.markdown("---")
        st.markdown("### Navigation")

        if st.button("Upload Data", use_container_width=True):
            st.session_state.current_page = "Upload"
            st.rerun()
        if st.button("Manual CSV to Excel", use_container_width=True):
            st.session_state.current_page = "Manual Workflow"
            st.rerun()
        if st.button("Stored Professors", use_container_width=True):
            st.session_state.current_page = "Stored Professors"
            st.rerun()

        if st.session_state.data_loaded:
            if st.button("Analytics", use_container_width=True):
                st.session_state.current_page = "Analytics"
                st.rerun()
            if st.button("Professor Directory", use_container_width=True):
                st.session_state.current_page = "Professor Directory"
                st.rerun()
            if st.session_state.current_page == "Professor Profile" and st.session_state.selected_professor:
                st.markdown("#### Current Professor")
                st.markdown(f"**{st.session_state.selected_professor}**")

        st.markdown("---")
        if st.button("Logout", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.data_loaded = False
            st.session_state.processor = None
            st.session_state.processed_df = None
            st.session_state.current_page = "Home"
            st.rerun()

        st.markdown("---")
        st.markdown(
            """
            ### Help

            **Upload Data:** Process raw Scopus CSV exports with affiliations

            **Manual CSV to Excel:** Convert a curated reporting CSV into the final Excel workbook

            **Stored Professors:** Review, edit, add, or delete saved professor records

            **Analytics:** Explore collaborations by country, year, institution, and professor
            """
        )

        st.markdown("---")
        if st.session_state.get("user_role") == "Admin":
            st.success("Admin mode active")
        else:
            st.info("Viewer mode active")

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
        show_upload_page()


st.markdown(
    """
    <style>
    :root {
        --bg: #f4f7fb;
        --surface: #ffffff;
        --surface-soft: #f7fafc;
        --border: #d8e2ec;
        --ink: #17324a;
        --muted: #5f7388;
        --accent: #0d5e8c;
        --accent-strong: #0a4a6e;
        --accent-soft: #e8f3fb;
        --shadow: 0 18px 48px rgba(23, 50, 74, 0.08);
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(224, 238, 248, 0.85), transparent 24%),
            linear-gradient(180deg, #f8fbfe 0%, #f1f6fb 100%);
        color: var(--ink);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fdfefe 0%, #eef4f9 100%);
        border-right: 1px solid var(--border);
    }
    .block-container {
        max-width: 1240px;
        padding-top: 2.2rem;
        padding-bottom: 2.5rem;
    }
    .hero-panel {
        background: linear-gradient(135deg, #ffffff 0%, #f0f7fd 100%);
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 2rem 2.2rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.2rem;
    }
    .hero-panel h1 {
        color: var(--ink);
        font-size: 2.3rem;
        line-height: 1.08;
        letter-spacing: -0.03em;
        margin: 0 0 0.75rem 0;
    }
    .hero-panel p {
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.75;
        max-width: 860px;
        margin: 0;
    }
    .eyebrow {
        color: var(--accent);
        font-size: 0.77rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
    }
    .info-card-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.5rem 0;
    }
    .info-card,
    .content-panel {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: var(--shadow);
    }
    .info-card {
        padding: 1.15rem 1.15rem 1.2rem 1.15rem;
    }
    .info-card-title {
        color: var(--ink);
        font-weight: 700;
        margin-bottom: 0.45rem;
        font-size: 0.98rem;
    }
    .info-card-body {
        color: var(--muted);
        line-height: 1.7;
        font-size: 0.95rem;
    }
    .content-panel {
        padding: 1.5rem 1.55rem;
        margin-top: 0.25rem;
    }
    .content-panel h3 {
        margin-top: 0;
        margin-bottom: 0.65rem;
        color: var(--ink);
    }
    .content-panel ul {
        margin: 0.2rem 0 0 1.1rem;
        color: var(--muted);
        line-height: 1.8;
    }
    h2, h3 {
        color: var(--ink);
        letter-spacing: -0.02em;
    }
    p, li, label, .stMarkdown, .stCaption {
        color: var(--muted);
    }
    .stMetric {
        background: linear-gradient(180deg, #ffffff 0%, #f4f8fc 100%);
        border: 1px solid var(--border);
        padding: 16px;
        border-radius: 16px;
        box-shadow: 0 12px 28px rgba(17, 51, 76, 0.06);
    }
    div[data-testid="stFileUploader"],
    div[data-testid="stDataFrame"],
    div[data-testid="stExpander"],
    div[data-testid="stForm"],
    div[data-baseweb="tab-list"] + div {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid var(--border);
        border-radius: 16px;
    }
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
        color: #ffffff;
        border: none;
        border-radius: 11px;
        font-weight: 600;
        padding: 0.65rem 1rem;
        box-shadow: 0 8px 18px rgba(13, 94, 140, 0.18);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(180deg, #156f9f 0%, #0d5a85 100%);
    }
    .stButton > button[kind="secondary"] {
        background: #ffffff;
        color: var(--ink);
        border: 1px solid var(--border);
        box-shadow: none;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        padding-bottom: 0.6rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.85);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 0.45rem 0.95rem;
    }
    .stAlert {
        border-radius: 14px;
    }
    @media (max-width: 900px) {
        .info-card-grid {
            grid-template-columns: 1fr;
        }
        .hero-panel {
            padding: 1.55rem;
        }
        .hero-panel h1 {
            font-size: 1.85rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

show_main_content()
