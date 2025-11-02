# Backend API and Dataset Migration

This document describes the consolidated dataset flow, versioning, and migration commands to maintain a single source of truth in the backend while ensuring backward compatibility and zero downtime.

## Unified Dataset API

- Endpoint: `GET /api/dataset/`
- Query params:
  - `minutesSightings` (default `60`) — window for recent sightings
  - `minutesAlerts` (default `120`) — window for recent alerts
- Response shape:
  - `vehicles`: array of vehicles with Nepali plates and Devanagari names
  - `sightings`: recent sighting stream
  - `alerts`: recent alerts

This endpoint consolidates data previously fetched via `/api/vehicles/`, `/api/sightings/recent/`, and `/api/alerts/recent/`.

## Dataset Versioning

- Model: `DatasetVersion` tracks dataset migrations with:
  - `version_label` (string)
  - `applied_at` (auto timestamp)
  - `notes` (text)
  - `records_vehicles`, `records_sightings`, `records_alerts` (counts)
- Visible in Django Admin.

## Migration and Import Commands

Run these in the `backend` directory:

- Migrate existing DB to Nepali plates/names while preserving relations:
  - `python manage.py migrate_nepali_dataset --version nepali-v1`
  - Optional dry-run: `python manage.py migrate_nepali_dataset --dry-run`

- Import consolidated dataset JSON from the frontend into the backend DB:
  - `python manage.py import_frontend_dataset --path ../frontend/public/data/nepali_processed_dataset.json --version import-YYYYMMDD`
  - Optional dry-run: `python manage.py import_frontend_dataset --dry-run`

- Remove legacy dataset files from backend to establish DB as source of truth:
  - `python manage.py cleanup_legacy_dataset --dir data`
  - Optional dry-run: `python manage.py cleanup_legacy_dataset --dry-run`

## Backward Compatibility and Zero Downtime

- The unified endpoint coexists with legacy endpoints during transition.
- Use `--dry-run` to validate integrity before changes.
- Apply migrations in maintenance windows if needed; endpoint behavior remains stable.
- CORS is configured for `http://localhost:3000` and `http://localhost:3001` development environments.

## Frontend Integration

- `frontend/src/lib/dataset.js` uses unified `GET /api/dataset/` exclusively (API-only).
- `DatasetViewer` enforces `source="api"` and removes the static JSON option.
- Map and dashboard continue consuming existing endpoints; dataset UI uses consolidated data.

### Single-Source Migration Notes

- Static dataset files under `frontend/public/data/` have been removed to prevent drift.
- Frontend code no longer fetches `/public/data/nepali_processed_dataset.json`.
- Ensure backend server is running at `http://127.0.0.1:8000` and frontend at `http://localhost:3000`.
- The environment variable `NEXT_PUBLIC_API_BASE` can override API base if needed.

## Validation Checklist

- Verify `/api/dataset/` returns 200 and includes `vehicles`, `sightings`, `alerts`.
- Confirm Devanagari rendering for names and Nepali plate formats.
- Test search/sort filters including province extraction (`१..७`).
- Perform load testing by increasing poll intervals and dataset size.

## Notes

- Ensure DB migrations are applied (`python manage.py migrate`).
- Admin view lists `DatasetVersion` entries and counts after imports/migrations.