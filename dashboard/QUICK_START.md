# Quick Start Guide - For Non-Technical Users

This guide is for anyone who wants to **run the dashboard on their computer** without needing to understand technical details.

## What You Need

- **Computer**: Windows, Mac, or Linux
- **Python**: Version 3.8 or higher ([Download here](https://www.python.org/downloads/))
  - When installing, **IMPORTANT**: Check the box "Add Python to PATH"
- **Time**: ~5 minutes for setup

## Installation (One Time Only)

### Step 1: Download the Dashboard Code

1. Click the green **Code** button on the GitHub repository
2. Click **"Download ZIP"**
3. Extract the ZIP file to a folder (e.g., `Documents/dashboard`)

### Step 2: Install Dependencies

1. Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux)
2. Navigate to your dashboard folder:
   ```
   cd path/to/your/dashboard
   ```
3. Copy and paste this command:
   ```
   pip install -r requirements.txt
   ```
4. Wait for it to finish (1-2 minutes)

## Running the Dashboard

Every time you want to use the dashboard:

### Step 1: Open Command Prompt / Terminal

### Step 2: Navigate to Dashboard Folder
```
cd path/to/your/dashboard
```

### Step 3: Start the Dashboard
```
streamlit run app.py
```

The dashboard will **automatically open in your browser**. If not, go to:
```
http://localhost:8501
```

## Using the Dashboard

### Simple Workflow (For Quick Work)

1. **Login**: Choose "Admin" or "Viewer" role
2. **Upload CSV**: Click "Upload Data" and select your Scopus CSV file
3. **View Results**: See the processed collaborations
4. **Export Excel**: Click "Download as Excel" to save as professional spreadsheet
5. **Done!** You have your data in Excel format

### Detailed Workflow (For Analysis)

1. **Upload Data**: As above
2. **View Analytics**: See charts and statistics
3. **Browse Professors**: See each professor's collaborations
4. **View Details**: Click on a professor to see full details
5. **Filter & Export**: Filter data and download exactly what you need

## Getting Your CSV File

### From Scopus (Easy - Recommended)

1. Go to [Scopus.com](https://www.scopus.com)
2. Search for an author (e.g., professor name)
3. Click "Documents" tab
4. Select publications (use Ctrl+A for all)
5. Click "Export all"
6. Choose **"CSV (All fields)"** ← IMPORTANT!
7. Save file

**DO NOT** use "CSV (Standard fields)" - you need all fields for affiliations!

## Troubleshooting

### "Command not found: streamlit"
- Make sure you ran `pip install -r requirements.txt` in the dashboard folder
- Make sure you're in the correct folder (use `cd` command)

### "Port 8501 is already in use"
- Close any other Streamlit instances
- Or use a different port: `streamlit run app.py --server.port 8502`

### "No international collaborations found"
- Check that your CSV has "Affiliations" column
- Make sure you exported with "All fields" from Scopus
- Try uploading a different author's data

### "Can't open the CSV file"
- Make sure the file is saved as `.csv` (not `.xlsx` or `.txt`)
- Try opening it in Excel first to verify it's valid

## Data Privacy

✅ **Your data is safe!**
- All processing happens on YOUR computer only
- No data is sent to external servers
- No data is permanently stored
- When you close the app, the data is gone

## Getting Help

**If something doesn't work:**

1. Take a screenshot of the error
2. Try the troubleshooting section above
3. Contact your IT administrator with the error message

---

## That's It! 

You're ready to use the dashboard. The most common workflow is:

```
1. Open Command Prompt
2. streamlit run app.py
3. Upload CSV
4. Download Excel
5. Close when done
```

**Enjoy!** 🎓
