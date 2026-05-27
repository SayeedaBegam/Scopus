# Application Configuration
# This file is used for both Streamlit and future React versions

APP_NAME = "UTN International Collaboration Dashboard"
APP_VERSION = "1.0.0"
APP_STAGE = "Prototype"

# UI Settings
THEME = "light"  # Can be "light" or "dark"
SIDEBAR_STATE = "expanded"

# Data Processing
MIN_AFFILIATION_LENGTH = 3
CONFIDENCE_THRESHOLD = 0.5

# Export Settings
EXCEL_FORMAT = "xlsx"
CSV_ENCODING = "utf-8-sig"
DATE_FORMAT = "%Y-%m-%d"

# Features
FEATURES = {
    "csv_upload": True,
    "excel_export": True,
    "charts": True,
    "professor_profiles": True,
    "role_based_access": True,
    "admin_editing": False,  # Coming soon
    "scopus_api": False,  # Coming in Phase 2
}

# Roles and Permissions
ROLES = {
    "admin": {
        "view_data": True,
        "export_csv": True,
        "export_excel": True,
        "edit_data": False,  # Phase 2
        "delete_data": False,  # Phase 2
        "manage_users": False,  # Phase 3
    },
    "viewer": {
        "view_data": True,
        "export_csv": True,
        "export_excel": True,
        "edit_data": False,
        "delete_data": False,
        "manage_users": False,
    },
}

# Database (for future use)
USE_DATABASE = False
DATABASE_TYPE = "sqlite"  # Could be "postgresql", "mysql", etc.
DATABASE_URL = "local"

# API Settings (for future Scopus integration)
ENABLE_SCOPUS_API = False
SCOPUS_API_TIMEOUT = 30
SCOPUS_API_RATE_LIMIT = 100  # Requests per minute

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/dashboard.log"

# Security
SESSION_TIMEOUT = 3600  # 1 hour in seconds
MAX_FILE_SIZE = 50  # MB
ALLOWED_FILE_TYPES = [".csv"]

print(f"✓ Configuration loaded: {APP_NAME} v{APP_VERSION}")
