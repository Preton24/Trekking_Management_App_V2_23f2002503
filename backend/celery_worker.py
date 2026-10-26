from celery import Celery

from app import create_app

# Build the Flask app so Celery tasks can use its config and database
flask_app = create_app()

celery = Celery(
    "trekking",
    broker=flask_app.config["CELERY_BROKER_URL"],
    backend=flask_app.config["CELERY_RESULT_BACKEND"],
)


class FlaskTask(celery.Task):
    """Runs every task inside the Flask app context, so db and config work in tasks."""

    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery.Task = FlaskTask

# Scheduled jobs (daily reminders, monthly reports) will be added to this later
celery.conf.beat_schedule = {}
celery.conf.timezone = "Asia/Kolkata"
