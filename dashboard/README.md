# UTN International Collaboration Dashboard

A simple Streamlit-based dashboard for tracking international joint publications between UTN (Universität für Technologie Niederösterreich) and global partner institutions.

## Quick Start (Non-Technical Users)

**See [QUICK_START.md](QUICK_START.md) for simple step-by-step instructions.**

---

## Features

### 📤 CSV Upload & Processing
- Upload Scopus publication exports as CSV
- Automatic detection of international collaborations  
- Smart country and institution detection
- One row per international partner per publication

### 📊 Professional Excel Export
- **Generate formatted Excel spreadsheets** with:
  - Professional styling and headers
  - Summary statistics
  - Multiple sheets (main data + country summary)
  - Ready for printing and presentations

### 🧾 Manual CSV to Excel Workflow
- Upload a cleaned collaboration CSV that follows the UTN joint-publications template
- Generate the final Excel workbook directly inside the dashboard
- Save generated Excel files locally under `dashboard/data/generated_reports`
- Reuse saved professor records without re-uploading the same file

### 👥 Professor Management
- Directory of all professors
- Individual professor profiles with statistics
- Collaboration metrics and trends
- Partner country/institution tracking

### 📈 Analytics & Visualizations
- Interactive charts (Plotly)
- Breakdown by country, year, institution
- Professor-wise collaboration metrics
- Real-time filtering

### 🔐 Role-Based Access
- **Admin**: Full editing, deletion, export
- **Viewer**: Read-only + download requests

---

## Tech Stack

- **Framework**: Streamlit
- **Data**: pandas, numpy
- **Visualization**: Plotly
- **Export**: openpyxl, xlsxwriter
- **Language**: Python 3.8+

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### 2. Installation

```bash
# Navigate to dashboard folder
cd dashboard

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Application

```bash
streamlit run app.py
```

Opens automatically in your browser at `http://localhost:8501`

---

## Usage Guide

### Basic Workflow

1. **Select Role**: Choose Admin or Viewer
2. **Upload CSV**: Export from Scopus and upload
3. **Download Excel**: Get professional spreadsheet with one click
4. **Done!**

### Detailed Usage

**Upload Page**
- Supports Scopus CSV exports
- Shows preview and validation
- Displays processing summary

**Analytics Page**
- View all collaborations
- Interactive charts
- Filter by professor/country
- Download as Excel or CSV

**Manual CSV to Excel**
- Upload the cleaned collaboration CSV format
- Save professor records to the local dashboard library
- Generate and save the Excel workbook

**Stored Professors**
- Review previously saved professor records
- Edit rows, add new rows, or delete a professor
- Load a stored professor directly into the analytics pages

**Professor Directory**
- Browse all professors
- See collaboration metrics
- Click to view detailed profile

**Professor Profile**
- Detailed analytics per professor
- Charts and statistics
- All collaborations listed
- Export specific professor data

---

## Excel Export Features

### What You Get

When you click **"Download as Excel"**, you get a professionally formatted spreadsheet with:

✅ **Title & Metadata**
- Report title
- Generation date
- Summary statistics

✅ **Summary Section**
- Total collaborations count
- Partner countries
- Partner institutions
- Professors involved

✅ **Formatted Data Table**
- 10 columns with all collaboration details
- Color-coded headers
- Borders and alignment
- Frozen header for scrolling
- Optimized column widths

✅ **Ready to Use**
- Print-friendly format
- Compatible with Excel, Google Sheets, Calc
- Professional appearance
- No further formatting needed

### Example Output

```
International Joint Publications - Overview

Generated: 2026-02-03 14:30

Summary Statistics
Total Collaborations:     45
Partner Countries:        12
Partner Institutions:     28
Professors:               3

[Data Table with professional formatting]
```

## CSV Format Requirements

The Scopus export must include these columns:
- **Authors**: Publication authors
- **Document Title** (or Title): Publication title
- **Year**: Publication year
- **Source Title**: Journal/conference name
- **Affiliations**: Author affiliations (critical)
- **DOI** (optional): Digital Object Identifier

**Note**: Make sure to export with "All fields" option from Scopus to include affiliations.

## Data Processing Logic

### International Collaboration Detection

1. **Parse Affiliations**: Splits multiple affiliations per author
2. **Country Detection**: Automatically identifies country from affiliation text
3. **Filter German Institutions**: Excludes publications where all partners are in Germany
4. **Generate Rows**: Creates one row per international partner institution
5. **Confidence Scoring**: Marks uncertain detections with "Needs Review" flag

### Supported Countries

The system recognizes 100+ countries including:
- European countries (Germany, Austria, Switzerland, UK, France, etc.)
- Asian countries (China, Japan, South Korea, India, etc.)
- Americas (USA, Canada, Brazil, etc.)
- Africa and Oceania regions

## Admin Features

### Table Editing (Planned)
- Edit institution names and departments
- Update country assignments
- Add custom notes

### Row Management
- Delete erroneous entries
- Bulk actions on filtered data

### Data Export
- Download cleaned and processed CSV
- Export with selected filters applied

## Viewer Features

### Data Access
- View all collaborations and statistics
- Filter and search data
- Download visualizations

### Download Requests
- Request access to full datasets
- Track request status
- Communicate with administrators

## Data Privacy & Security

- **Local Processing**: All data is processed in your browser session
- **No Persistent Storage**: Data is not permanently stored on external servers
- **Session-Based**: Each session is independent and isolated
- **No External API Calls**: This prototype processes locally uploaded files only

## Troubleshooting

### "No international collaborations found"
- Ensure your CSV includes the "Affiliations" column
- Check if all partner institutions are German (filtered out)
- Verify column names match expected format

### "Cannot find Affiliations column"
- Make sure to export with "All fields" from Scopus
- Check for alternate column names (Author Affiliations, etc.)
- Verify CSV encoding is UTF-8

### Charts not displaying
- Ensure data has valid Year values
- Check that sufficient data points exist
- Refresh the page and re-upload if necessary

## Future Enhancements

### Phase 2 (Coming Soon)
- ✅ Table row editing interface
- ✅ Bulk delete functionality  
- ✅ Advanced filtering UI
- ✅ Department/Lab tracking

### Phase 3
- 🔄 Scopus API integration for direct data fetching
- 📧 Email notifications for new collaborations
- 📁 Project-based organization
- 🔗 Network visualization
- 📈 Advanced analytics and ML-based collaboration prediction

## Project Structure

```
dashboard/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # This file
│
├── utils/
│   ├── __init__.py
│   ├── data_processor.py    # CSV processing logic
│   ├── manual_processor.py  # Manual cleaned-CSV workflow
│   ├── storage.py           # Local saved professor/report storage
│   ├── country_detector.py  # Country/institution detection
│   └── ui_utils.py          # Chart and UI utilities
│
├── pages/                   # Individual page modules (reference)
│   ├── 1_home.py
│   ├── 2_upload.py
│   ├── 3_analytics.py
│   ├── 4_professor_directory.py
│   └── 5_professor_profile.py
│
└── data/                    # Sample data directory (for future use)
```

## Development Notes

### Adding New Countries
Edit `utils/country_detector.py` and add entries to `COUNTRIES_MAP`:

```python
COUNTRIES_MAP = {
    'CountryName': ['CountryName', 'variation1', 'variation2'],
    # ...
}
```

### Customizing Detection Logic
Modify `process_affiliations()` in `country_detector.py` to adjust:
- How institutions are extracted from affiliation strings
- How countries are detected
- Confidence scoring logic

### Extending the Dashboard
Add new pages by:
1. Creating a new function in `app.py`
2. Adding a navigation button in `show_main_content()`
3. Adding page routing logic

## Support & Contact

For questions, issues, or feature requests, please contact:
- UTN Administration Team
- Dashboard Development Team

## License

This project is developed for UTN (Universität für Technologie Niederösterreich).
Internal use only.

## Version

**Version**: 1.0.0 (Prototype)  
**Last Updated**: February 2026  
**Status**: Active Development
