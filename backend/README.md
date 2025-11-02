# APF ALPR Smart Monitoring — Backend

- Purpose: Django REST API powering Nepal Police ALPR smart monitoring — vehicles, sightings, alerts, verification, and consolidated dataset. Supports Devanagari/Nepali plates and names.
- Tech Stack: Python 3.9, Django 4.2, Django REST Framework, sqlite3, `django-cors-headers`.
- Key APIs:
  - `GET /api/vehicles/`
  - `GET /api/sightings/recent/?minutes=<N>`
  - `GET /api/alerts/recent/?minutes=<N>`
  - `POST /api/alerts/{id}/acknowledge/`
  - `GET /api/dataset/`
  - `POST /api/verify/`
- Development:
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt` (or install `django djangorestframework django-cors-headers`)
  - `python manage.py migrate`
  - `python manage.py runserver 127.0.0.1:8000`
- CORS: Allow dev origins like `http://localhost:3000` and `http://localhost:3001` when calling from the browser.
- Admin: Django Admin at `http://127.0.0.1:8000/admin`.