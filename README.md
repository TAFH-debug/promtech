# PromTech

PromTech is a full-stack pipeline integrity/inspection dashboard: import inspection data, visualize objects on a map, browse analytics, and generate PDF reports (with an optional AI assistant powered by Gemini).

## Tech Stack

- Frontend: Next.js (App Router) + TypeScript + Tailwind + HeroUI + Leaflet
- Backend: FastAPI + SQLModel + PostgreSQL

## Repository Layout

- `frontend/` - Next.js web app
- `backend/` - FastAPI API server
- `misc/` - sample datasets + generators

## Requirements

- Node.js 18+ (or 20+) + npm
- Python 3.10+ + pip
- PostgreSQL (or another DB supported by SQLAlchemy/SQLModel via `DATABASE_URL`)

## Quickstart

`DATABASE_URL` is required (the backend creates the SQLAlchemy engine at import-time).

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/promtech
# Optional (enables /api/v1/bot/chat)
GEMINI_API_KEY=your_key_here
```

```powershell
python run.py
```

```powershell
cd frontend
npm install
```
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```
```powershell
npm run dev
```

## Useful API Endpoints

- Import CSV/XLSX: `POST /api/v1/csv/import/` (max 5MB)
- Map objects: `GET /api/v1/map-objects`
- Dashboard stats: `GET /api/v1/dashboard/stats`
- ML metrics: `GET /api/v1/ml/metrics`
- PDF report: `POST /api/v1/reports/{pipeline_id}/pdf`
- AI bot chat (requires `GEMINI_API_KEY`): `POST /api/v1/bot/chat`

## Sample Data

- `misc/objects.csv`
- `misc/diagnostic_data.csv`
- Generators: `misc/database_generator.py`, `misc/diagnostics_generator.py`
