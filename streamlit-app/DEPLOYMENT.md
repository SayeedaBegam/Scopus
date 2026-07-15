# Deployment Guide

This guide explains how to run the dashboard locally and prepare it for deployment.

## Local Development (Your Computer)

### Quick Start (Recommended)

```powershell
# Open PowerShell and navigate to dashboard folder
cd path\to\dashboard

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

**That's it!** The dashboard opens automatically in your browser.

---

## Local Network Sharing (Multiple Computers)

To share the dashboard with others on your office network:

### Step 1: Find Your Computer's IP Address

```powershell
ipconfig
```

Look for "IPv4 Address" (usually starts with 192.168 or 10.x.x.x)
Example: `192.168.1.100`

### Step 2: Expose Dashboard

Modify `~/.streamlit/config.toml`:

```ini
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[client]
serverAddress = "0.0.0.0"
```

### Step 3: Start App

```powershell
streamlit run app.py --server.address=0.0.0.0
```

### Step 4: Others Connect

Other computers on your network can access:
```
http://YOUR_IP:8501
```

Example: `http://192.168.1.100:8501`

---

## Cloud Deployment (For Later)

When you're ready to deploy to the cloud:

### Option 1: Streamlit Cloud (Easiest - Free)

1. Push code to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub account
4. Select repository and branch
5. Deploy automatically ✓

**Pros**: Free, automatic updates, easy
**Cons**: Requires GitHub, limited computing power

### Option 2: Heroku (Moderate - Free tier deprecated)

Would require:
- Heroku account
- `Procfile` and `runtime.txt` files
- BuildPacks configuration

### Option 3: AWS / Azure / Google Cloud (Most Control)

For enterprise deployment:
- EC2 / App Service / Compute Engine instance
- Docker containerization
- CI/CD pipeline
- Custom authentication
- SSL certificates

---

## Docker Deployment (For Technical Teams)

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

Create `.dockerignore`:

```
venv/
__pycache__/
*.pyc
.git/
.gitignore
*.csv
*.xlsx
```

Build and run:

```bash
docker build -t utn-dashboard .
docker run -p 8501:8501 utn-dashboard
```

---

## Environment Variables (For Secrets)

Create `.env` file (not in GitHub):

```
ADMIN_PASSWORD=your_secure_password
API_KEY=your_api_key
DATABASE_URL=your_db_url
```

Load in app:

```python
from dotenv import load_dotenv
import os

load_dotenv()
admin_password = os.getenv("ADMIN_PASSWORD")
```

---

## Performance Optimization

### Caching (Speed Up Dashboard)

```python
import streamlit as st

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

# Function results are cached
df = load_data("data.csv")
```

### Session State

```python
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
```

---

## Monitoring & Logging

Create `logs/dashboard.log`:

```python
import logging

logging.basicConfig(
    filename='logs/dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Dashboard started")
```

---

## Scaling for Multiple Users

### Current Setup (Development)
- ✓ Works for 1-5 users
- Uses local processing
- No database

### For 5-20 Users
- Keep Streamlit
- Add lightweight caching
- Monitor resource usage
- Increase session timeouts

### For 20+ Users
- Consider migrating to React + FastAPI backend
- Add database (PostgreSQL)
- Implement user authentication
- Set up load balancing

---

## Security Considerations

### Before Public Deployment

1. **Remove Debug Mode**
   ```python
   st.set_page_config(..., logger_level="error")
   ```

2. **Validate All Inputs**
   - File size limits
   - CSV validation
   - XSS prevention

3. **Enable HTTPS**
   - Use SSL/TLS certificates
   - Redirect HTTP to HTTPS

4. **Rate Limiting**
   - Limit uploads per hour
   - Throttle API calls

5. **Data Privacy**
   - Encrypt sensitive files
   - Regular backups
   - Data retention policy

---

## Troubleshooting

### Port Already in Use
```powershell
streamlit run app.py --server.port 8502
```

### Out of Memory
- Increase Python memory
- Process files in chunks
- Use streaming uploads

### Slow Performance
- Enable caching
- Optimize CSV processing
- Use lighter dataframes

---

## Roadmap for Production

```
Phase 1 (Current) ✓
├─ Streamlit prototype
├─ Local CSV processing
└─ Excel export

Phase 2 (Next)
├─ Add database
├─ User authentication
├─ Scopus API integration
└─ Advanced editing

Phase 3 (Future)
├─ React frontend
├─ FastAPI backend
├─ Cloud deployment
└─ Mobile app
```

---

## Next Steps

1. **Test locally** with sample data
2. **Share with team** via network or GitHub
3. **Collect feedback** on Excel output format
4. **Plan Phase 2** when ready for full production
5. **Set up GitHub** repository (see GITHUB_SETUP.md)

---

**Questions?** See README.md or contact your development team.
