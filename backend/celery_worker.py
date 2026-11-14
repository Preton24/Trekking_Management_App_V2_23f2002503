"""Entry point for the Celery worker and Celery beat.

Run both from the backend/ folder:
    celery -A celery_worker.celery worker --loglevel=info
    celery -A celery_worker.celery beat --loglevel=info

"-A celery_worker.celery" means: import this file and use the variable `celery`.
"""
from app import create_app

# Building the Flask app also builds the Celery object (see init_celery in
# celery_utils.py), whose tasks run inside this app's context so they can use
# the models and the config.
flask_app = create_app()
celery = flask_app.extensions["celery"]

# Importing tasks.py registers its tasks with the worker
import tasks  # noqa: E402,F401
