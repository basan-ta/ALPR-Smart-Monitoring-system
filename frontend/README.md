# APF ALPR Smart Monitoring — Frontend

- Purpose: Next.js dashboard for live monitoring — Map, Alerts, Vehicles, Stats, and Dataset viewer. Displays Nepali plates and Devanagari names.
- Tech Stack: Next.js 16, React 19, React Leaflet, Tailwind CSS 4.
- API Setup:
  - Proxies `GET /api/*` to the backend via rewrites in `next.config.mjs`.
  - Use `BACKEND_ORIGIN` to point to your backend (defaults to `http://127.0.0.1:8000`).
  - Client helpers read `NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_API_BASE` if set.
- Development:
  - `npm install`
  - `BACKEND_ORIGIN=http://127.0.0.1:8000 npm run dev`
  - Open `http://localhost:3000`
- UI Panels: `AlertsPanel`, `VehiclesTable`, `StatsPanel`, `MapPanel`, `DatasetViewer` with loading and error feedback.
- Admin: NavBar includes a link to Django Admin at the backend origin.
