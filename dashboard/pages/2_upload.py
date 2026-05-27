"""
CSV Upload and Processing page.
"""

import streamlit as st
import pandas as pd
from utils.data_processor import ScopusCSVProcessor
import io


def show_upload_page():
    """Display CSV upload interface."""
    
    st.markdown("## 📤 Upload Publication Data")
    
    st.markdown("""
    Upload a Scopus CSV export containing publication information and author affiliations.
    The system will automatically extract international collaborations.
    """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file from Scopus export",
        type="csv",
        help="Download from Scopus: Menu → Export → CSV (All fields)"
    )
    
    if uploaded_file is not None:
        st.markdown("---")
        
        # Show upload progress
        with st.spinner("Processing your file..."):
            # Initialize processor
            processor = ScopusCSVProcessor()
            
            # Load CSV
            success, message = processor.load_csv(uploaded_file)
            
            if success:
                st.success(message)
                
                # Show available columns
                with st.expander("📋 Detected columns in your CSV"):
                    columns = processor.get_available_columns()
                    st.write(f"Total columns detected: {len(columns)}")
                    cols_display = ", ".join(columns)
                    st.caption(cols_display)
                
                # Show preview of raw data
                with st.expander("👁️ Preview of raw data"):
                    st.dataframe(processor.raw_df.head(5), use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Processing Data")
                
                # Process the data
                process_success, process_message = processor.process()
                
                if process_success:
                    st.success(f"✅ {process_message}")
                    
                    # Store processor in session state
                    st.session_state.processor = processor
                    st.session_state.processed_df = processor.get_processed_df()
                    st.session_state.data_loaded = True
                    
                    # Show statistics
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
                    
                    # Show preview of processed data
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
        # Show instructions if no file uploaded
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


if __name__ == "__main__":
    show_upload_page()
