# CLAUDE.md — Trekking Management Application (MAD2, IIT Madras)

This is a course project for Modern Application Development II (MAD2) at IIT Madras.
The code will be explained in a viva, so every choice must be simple and defensible.

## Allowed stack (ONLY these — no exceptions)

| Purpose            | Technology                          |
|--------------------|-------------------------------------|
| Backend API        | Flask                               |
| Frontend UI        | Vue.js 3                            |
| Styling            | Bootstrap 5                         |
| Database           | SQLite via Flask-SQLAlchemy         |
| Caching            | Redis                               |
| Background jobs    | Celery with Redis as broker/backend |
| Charts             | ChartJS                             |

- Do NOT add any other frameworks, UI kits, or CSS libraries (no Tailwind, Vuetify, jQuery, etc.).
- Use the browser's built-in `fetch()` for HTTP calls. Do NOT use Axios.
- If a task seems to need something outside this list, stop and ask first.

## Folder structure (required)

```
frontend/
  src/          # app entry, router, views/pages
  components/   # reusable Vue components — sits BESIDE src/, not inside it
backend/
  app.py        # Flask app entry point
  models/       # SQLAlchemy models
  routes/       # API route blueprints
```

Keep components in `frontend/components/`, never `frontend/src/components/`.

## User roles

- **Admin** — exactly one. Seeded in code at startup (not via a signup form).
- **Trek Staff** — accounts are created by the Admin. Staff can only log in; there is no staff self-registration.
- **Trekker** — registers themselves through the signup page.

Enforce role checks on the backend for every protected route; the frontend hiding a button is not security.

## Database rules

- The database must be created programmatically with `db.create_all()` (inside an app context) on startup.
- Never create tables or the `.db` file manually, and never commit hand-written SQL schema.
- Admin seeding happens in code right after `db.create_all()`, and must not duplicate the admin if one already exists.

## Coding style

- Simple, readable, well-commented code that a student can explain line by line in a viva.
- Prefer clarity over cleverness: explicit loops over dense one-liners, descriptive names, small functions.
- Comment the *why* of each block (e.g. why a route is cached, why a task is async).
- Avoid unnecessary abstractions, metaprogramming, or patterns that are hard to justify.

## Working agreement

- After making any change, briefly explain what was changed and why.

## Dev environment (macOS)

- Redis is installed via Homebrew: `brew services start redis` (default port 6379).
- Flask runs on **port 5001** — port 5000 is taken by macOS AirPlay Receiver.
  Run with `app.run(port=5001, debug=True)` or `flask run --port 5001`.
- The frontend must point its `fetch()` base URL at `http://localhost:5001`.
- Celery (from `backend/`): `celery -A celery_worker.celery worker --loglevel=info` and `celery -A celery_worker.celery beat --loglevel=info`.
