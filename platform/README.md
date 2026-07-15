# UTN International Research Collaboration Dashboard

Production-oriented monorepo for identifying UTN publications in Scopus, excluding German affiliations, reviewing uncertain institution mappings, analysing international partnerships, and exporting governed Excel reports.

The previous Streamlit prototype is isolated in `../streamlit-app/`. The supported full-stack application is this folder's `frontend/` + `backend/`.

## Architecture

- **Next.js/TypeScript/Tailwind** frontend, with role-aware navigation and accessible forms.
- **FastAPI/SQLAlchemy/Alembic** API. HttpOnly JWT cookies are used for browser sessions; every privileged endpoint also enforces roles server-side.
- **PostgreSQL** is the system of record. EID, link-table, alias, and collaboration constraints make synchronization idempotent.
- **Celery/Redis/Beat** runs weekly incremental updates. Manual updates use the identical service.
- **Scopus adapter** supports live Elsevier APIs and quota-free realistic mock data. API credentials never reach the browser.
- Raw publication JSON and raw affiliation text are retained. Deterministic resolution excludes Germany and UTN; uncertainty creates review items.

See [architecture details](docs/ARCHITECTURE.md) and the [entity relationship diagram](docs/ERD.md).

For the temporary no-card deployment using Netlify, Render, and Neon, follow [the free deployment guide](docs/FREE_DEPLOYMENT.md). The cloud demo uses direct/manual synchronization plus an optional protected GitHub schedule; the local Docker Compose stack continues to use Redis and Celery.

## Quick start

1. Copy `.env.example` to `.env`.
2. Set `SECRET_KEY`, `POSTGRES_PASSWORD`, `SEED_ADMIN_PASSWORD`, and `SEED_VIEWER_PASSWORD`.
3. For live mode set `SCOPUS_MODE=live`, `ELSEVIER_API_KEY`, and optionally `ELSEVIER_INST_TOKEN`. Keep `mock` for a quota-free demo.
4. Start: `docker compose up --build -d`.
5. Migrate: `docker compose exec backend alembic upgrade head`.
6. Seed: `docker compose exec backend python -m app.seed`.
7. Open <http://localhost:3000>. API documentation is at <http://localhost:8000/docs>.
8. Sign in with `admin@utn.de` or `viewer@utn.de` and the passwords you placed in `.env`.

### User accounts

After signing in as an administrator, open **Manage accounts**. Create a separate account for every administrator, reviewer, and viewer using their institutional email address and a temporary password of at least 12 characters. Administrators can reset passwords and deactivate accounts from the same page. Viewer accounts can browse professors and analytics but cannot change data; their export requests require administrator approval.

Do not share one administrator login between several people. Separate accounts keep the audit log attributable and can be disabled individually when access changes.
9. Add a professor, confirm their Scopus Author ID, select **Update from Scopus**, resolve **Needs review**, and export the report.

Development fallback credentials are only used if seed password variables are absent: `DevAdmin!Change2026` and `DevViewer!Change2026`. Never use these in a shared or production environment.

## Commands

```powershell
# Backend without Docker (uses SQLite unless DATABASE_URL is set)
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -m app.seed
.venv\Scripts\uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend
pytest -q
cd ../frontend
npm run build
```

## Environment variables

All supported variables and safe placeholders are in `.env.example`. Important groups are database/Redis URLs, session `SECRET_KEY`, CORS origins, Scopus mode and Elsevier credentials, request timeout/retries, CSV size limit, export directory, and configurable UTN names/affiliation IDs.

## Database migrations

`alembic upgrade head` applies the schema. Create reviewed migrations with `alembic revision --autogenerate -m "description"`; inspect generated SQL before applying it. Do not use `Base.metadata.create_all` outside the seed convenience path.

## CSV fallback

The import flow detects UTF-8/Latin-1, comma/semicolon/tab delimiters, and common Scopus column names. It first returns mapping, missing fields, and ten preview rows; confirmation is a separate request. See `samples/scopus-import-sample.csv`.

## Production notes

- Terminate TLS at a trusted reverse proxy and set `ENVIRONMENT=production` so the session cookie is Secure.
- Store secrets in the deployment secret manager, rotate Elsevier/API and session credentials, restrict database/Redis network access, and back up PostgreSQL and approved exports.
- Run migrations as a release job before rolling out API/worker containers. Run at least two workers where synchronization volume requires it.
- Add institutional SSO by replacing the authentication provider while preserving `current_user` and role dependencies.
- Configure retention rules for raw Scopus metadata, audit logs, and generated exports with UTN data governance.

## Troubleshooting

- **401 from Scopus:** API key is missing/invalid. **403:** the key lacks the required entitlement. **429:** wait until the response quota reset; the client records quota headers and retries temporary failures.
- **No international rows:** all affiliations may be German/UTN. Unknown countries appear in **Needs review**, not in the collaboration dataset.
- **CSV rejected:** use `.csv`, stay under `MAX_CSV_BYTES`, and include title, year, and affiliations. The preview lists missing fields.
- **Frontend cannot reach API:** verify `BACKEND_INTERNAL_URL=http://backend:8000` in Compose and inspect `docker compose logs backend frontend`.

## Credentials-dependent items

Live Scopus response shapes, UTN's authoritative affiliation IDs/name aliases, institutional API entitlements, deployment SSO, mail delivery for password reset/approval notifications, and final retention/access policy require UTN or Elsevier input. Mock mode covers the end-to-end workflow without those inputs.
