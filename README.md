# Trekking Management Application (MAD2, IIT Madras)

Flask API + Vue 3 (Vite) frontend, SQLite, Redis caching, Celery background jobs.

## Folder structure

```
backend/
  app.py            # Flask app factory + Config class
  celery_worker.py  # Celery app (worker + beat)
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