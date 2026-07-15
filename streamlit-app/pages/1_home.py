"""
Home/Login page - Role selector and application overview.
"""

import streamlit as st
import os


def show_login_page():
    """Display login/role selector page."""
    
    # Center content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🎓 UTN International Collaboration Dashboard")
        st.markdown("### Welcome!")
        st.markdown("---")
        
        # Role selector
        st.markdown("#### Select Your Role")
        role = st.radio(
            "Choose your role:",
            ["Admin", "Viewer"],
            horizontal=False,
            help="Admin: Full access to upload, edit, and export data. Viewer: View-only access."
        )
        
        st.session_state.user_role = role
        
        st.markdown("---")
        
        # Application description
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
            st.session_state.page = "upload"
            st.rerun()
        
        st.markdown("""
        ---
        **Data Privacy Notice:** All data is processed locally in your browser session.
        No data is permanently stored on external servers.
        """)


if __name__ == "__main__":
    show_login_page()
