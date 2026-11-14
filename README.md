# Trekking Management Application (MAD2, IIT Madras)

Flask API + Vue 3 (Vite) frontend, SQLite, Redis caching, Celery background jobs.

## Folder structure

```
backend/
  app.py            # Flask app factory + Config class
  celery_utils.py   # builds the Celery object + beat schedule (called from create_app)
  celery_worker.py  # entry point for the Celery worker and beat
  tasks.py          # Celery tasks: daily reminders, monthly report, CSV export
  templates/        # Jinja template for the monthly report email
  static/exports/   # CSV files written by the export task (not committed)
  models/           # SQLAlchemy models (db = SQLAlchemy() in __init__.py)
  routes/           # API blueprints
  requirements.txt
frontend/
  src/              # main.js, router.js, App.vue, config.js
  components/       # page components (beside src/, imported as @components/...)
```

## One-time setup

### Python virtual environment (backend)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # run this in every new terminal before backend commands
pip install -r requirements.txt
```

To leave the venv later: `deactivate`.

### Frontend dependencies

```bash
cd frontend
npm install
```

### Redis (macOS, Homebrew)

```bash
brew install redis
```

## Running the app

Use a separate terminal for each. Backend terminals need the venv active and must be run from `backend/`.

| What          | Command                                                      |
|---------------|--------------------------------------------------------------|
| Redis         | `brew services start redis` (stop: `brew services stop redis`) |
| Flask API     | `cd backend && python app.py` → http://localhost:5001        |
| Vite frontend | `cd frontend && npm run dev` → http://localhost:5173         |
| Celery worker | `cd backend && celery -A celery_worker.celery worker --loglevel=info` |
| Celery beat   | `cd backend && celery -A celery_worker.celery beat --loglevel=info`   |

Flask uses port **5001** because macOS AirPlay Receiver uses port 5000.

The SQLite database is created automatically at `backend/instance/trekking.db` by `db.create_all()` when Flask starts.

Check it works: open http://localhost:5173. The page should say "Backend status: ok".


## 1. Start Redis
Redis is used for caching and Celery message brokering. Start it with Homebrew:


brew services start redis
(To stop later: brew services stop redis)

### 2. Run the Flask Backend (Port 5001)
In a new terminal:


cd backend
source venv/bin/activate
# (Optional) Seed demo data (2 staff, 3 trekkers, 5 sample treks):
python seed.py
# Start the Flask development server:
python app.py


## 3. Run the Vue 3 Frontend (Port 5173)
In another terminal:

bash
cd frontend
npm run dev


## 4. Background Tasks (Celery Worker & Beat) — Optional
If you are running background jobs or scheduled reports:

### Celery Worker (in a new terminal):


cd backend
source venv/bin/activate
celery -A celery_worker.celery worker --loglevel=info
Celery Beat (in a new terminal):


cd backend
source venv/bin/activate
celery -A celery_worker.celery beat --loglevel=info


## Celery jobs

`backend/tasks.py` has three tasks:

| Task                   | Started by                              | What it does |
|------------------------|-----------------------------------------|--------------|
| `send_daily_reminders` | Celery beat, every day (default 08:00)  | Posts a Google Chat reminder for every active booking on a trek starting in the next 2 days |
| `send_monthly_report`  | Celery beat, 09:00 on day 1 of a month  | Emails the admin an HTML report with the same report attached as a PDF: treks conducted last month, participants, top 3 popular treks |
| `export_bookings_csv`  | A trekker clicking **Export CSV**       | Writes the trekker's bookings to `backend/static/exports/`, then posts a Google Chat alert |

CSV export flow: `POST /api/bookings/export` replies with a `task_id` → the dashboard calls
`GET /api/tasks/<task_id>` every 2 seconds → when the state is `SUCCESS` the reply has a
`download_url` and the toast shows a **Download CSV** button.

### Settings (`.env` in the project root)

Copy `.env.example` to `.env` and fill it in. The app reads `.env` by itself on startup,
so nothing needs to be exported in the terminal.

| Variable                  | Meaning                                                        |
|---------------------------|----------------------------------------------------------------|
| `GOOGLE_CHAT_WEBHOOK_URL` | Webhook URL of the Google Chat space                           |
| `MAIL_*`                  | Gmail address and app password used to send the monthly report |
| `MONTHLY_REPORT_EMAIL`    | Where the report goes; empty = the admin account's email       |
| `REMINDER_HOUR`           | Hour the daily job runs, 0-23, Indian time (default `8`)       |
| `REMINDER_MINUTE`         | Minute the daily job runs, 0-59 (default `0`)                  |
| `DEMO_MODE`               | `true` runs every scheduled job once a minute (for the viva)   |

Restart the worker **and** beat after changing `.env`; they only read it when they start.

### Commands (macOS, Redis from Homebrew)

Use three terminals.

Terminal 1, Redis:

```bash
brew services start redis
redis-cli ping          # should print PONG
```

Terminal 2, Celery worker (runs the tasks):

```bash
cd backend
source venv/bin/activate
celery -A celery_worker.celery worker --loglevel=info
```

Terminal 3, Celery beat (sends the tasks on schedule):

```bash
cd backend
source venv/bin/activate
celery -A celery_worker.celery beat --loglevel=info
```

To run a scheduled task once, right now, without waiting for beat (the worker must be running):

```bash
cd backend
source venv/bin/activate
celery -A celery_worker.celery call tasks.send_daily_reminders
celery -A celery_worker.celery call tasks.send_monthly_report
```

### Demo for the viva

1. Set `DEMO_MODE=true` in `.env`.
2. Make sure a trekker has a booking on a trek that starts tomorrow or the day after.
3. Start the worker and beat. Within a minute the worker log shows
   `Task tasks.send_daily_reminders ... succeeded` and the message appears in the Google Chat space.
4. The monthly report email also arrives every minute in demo mode.
5. For the CSV export, log in as a trekker, click **Export CSV** on the dashboard and watch the toast
   change from "Preparing" to a **Download CSV** button. This needs the worker, but not beat.
6. Set `DEMO_MODE=false` again afterwards, otherwise the reminder and the report repeat every minute.
