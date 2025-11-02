# APF ALPR Smart Monitoring System

Full‑stack ALPR monitoring for Nepal Police: a Django REST API backend with a Next.js dashboard frontend. It tracks vehicles, live sightings, and alerts, supports Nepali (Devanagari) plates and names, and provides a consolidated dataset view.

## Tech Stack
- Backend: Python 3.9, Django 4.2, Django REST Framework, sqlite3, `django-cors-headers`
- Frontend: Next.js 16, React 19, Tailwind CSS 4, Leaflet/React‑Leaflet

## Project Structure
- `backend/` — Django REST API (vehicles, sightings, alerts, verification, dataset)
- `frontend/` — Next.js dashboard (Map, Alerts, Vehicles, Stats, Dataset viewer)

## Quick Start
Prerequisites: Python 3.9+, Node.js 18+.

Backend (API)
1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt` (or install `django djangorestframework django-cors-headers`)
4. `python manage.py migrate`
5. `python manage.py runserver 127.0.0.1:8000`
   - Admin: `http://127.0.0.1:8000/admin`
   - CORS: ensure dev origins like `http://localhost:3000` (and `http://localhost:3001` if needed) are allowed in `backend/backend/settings.py`.

Frontend (Dashboard)
1. `cd frontend`
2. `npm install`
3. `BACKEND_ORIGIN=http://127.0.0.1:8000 npm run dev`
4. Open `http://localhost:3000`
   - `/api/*` calls are proxied to the backend via `next.config.mjs`.
   - Client helpers can also read `NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_API_BASE` if set.

## Key API Endpoints
- `GET /api/vehicles/`
- `GET /api/sightings/recent/?minutes=<N>`
- `GET /api/alerts/recent/?minutes=<N>`
- `POST /api/alerts/{id}/acknowledge/`
- `GET /api/dataset/` (consolidated vehicles, sightings, alerts)
- `POST /api/verify/`

## UI Panels
- MapPanel — live map of recent sightings
- AlertsPanel — recent alerts with acknowledge action
- VehiclesTable — searchable/filterable vehicle list
- StatsPanel — live stats with animated changes
- DatasetViewer — unified dataset with filters and sorting

## Optional Backend Commands
- Backup: `python manage.py backup_backend_data --output backup.json`
- Validate dataset JSON: `python manage.py validate_frontend_dataset --path <file> --output report.json`
- Import dataset JSON: `python manage.py import_frontend_dataset --path <file> --version <label>`

## Notes
- Root `.gitignore` covers Python/Django + Node/Next.js artifacts.
- Next.js rewrites proxy `/api/*` to the backend; configure `BACKEND_ORIGIN` for environments.