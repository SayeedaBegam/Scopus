# UTN Scopus applications

This workspace is separated into independent applications and shared source material.

```text
Scopus/
├── streamlit-app/       Legacy standalone Streamlit dashboard
├── platform/            Complete Next.js + FastAPI architecture
│   ├── frontend/        Next.js user interface
│   ├── backend/         FastAPI, SQLAlchemy, Celery and tests
│   ├── docs/            Architecture and database diagrams
│   ├── samples/         Example CSV and Excel export
│   └── docker-compose.yml
├── shared/
│   └── source-data/     Original project CSV and PDF
└── .devcontainer/       Repository-wide development container
```

## Run the new full-stack platform

Docker is the recommended method because it starts the frontend, backend, PostgreSQL, Redis, worker and scheduler together.

```powershell
cd C:\Users\sayee\Downloads\Scopus\platform
Copy-Item .env.example .env
```

Edit `.env` and replace `SECRET_KEY`, `POSTGRES_PASSWORD`, `SEED_ADMIN_PASSWORD` and `SEED_VIEWER_PASSWORD`. Keep `SCOPUS_MODE=mock` for the included demonstration data.

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Then open:

- New web application: <http://localhost:3000>
- Backend API documentation: <http://localhost:8000/docs>

Sign in as `admin@utn.de` or `viewer@utn.de` with the passwords you entered in `.env`.

To stop it:

```powershell
docker compose down
```

For live Scopus data, stop the application, set `SCOPUS_MODE=live` and `ELSEVIER_API_KEY` in `platform/.env`, then start it again.

Full setup, production and troubleshooting documentation is in [platform/README.md](platform/README.md).

For a temporary 2–3 month no-card deployment, use the [Netlify + Render + Neon deployment guide](platform/docs/FREE_DEPLOYMENT.md).

## Run only the backend locally

```powershell
cd C:\Users\sayee\Downloads\Scopus\platform\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:SCOPUS_MODE = "mock"
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python -m app.seed
.\.venv\Scripts\uvicorn app.main:app --reload
```

The backend will be available at <http://localhost:8000/docs>.

## Run the legacy Streamlit application

```powershell
cd C:\Users\sayee\Downloads\Scopus\streamlit-app
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\streamlit run app.py
```

Open <http://localhost:8501>. This application is retained for the original CSV-based workflow; new development should use `platform/`.

## Tests

```powershell
cd C:\Users\sayee\Downloads\Scopus\platform\backend
.\.venv\Scripts\python -m pytest -q
```
