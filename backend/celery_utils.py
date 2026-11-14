"""Creates the Celery object and connects it to the Flask app.

Redis is both the broker (the queue that task messages wait in) and the result
backend (where each task's state and return value are stored).

This lives in its own file, and create_app() calls init_celery(app), because two
different programs need the same Celery object:
  - the Flask server, to PUT a task on the queue (the CSV export button) and to
    read a task's status afterwards
  - the Celery worker and beat (started through celery_worker.py), to RUN tasks
"""
from celery import Celery, Task
from celery.schedules import crontab

# How often every scheduled job runs when DEMO_MODE is on
DEMO_INTERVAL_SECONDS = 60.0


def pick_schedule(app, normal_schedule):
    """Return the real schedule, or "every 1 minute" when DEMO_MODE is on.

    Every entry in beat_schedule goes through this function, so one flag
    speeds up all scheduled jobs for the viva and nothing else has to change.
    """
    if app.config["DEMO_MODE"]:
        return DEMO_INTERVAL_SECONDS
    return normal_schedule


def init_celery(app):
    """Build the Celery object for this Flask app and store it in app.extensions["celery"]."""

    class FlaskTask(Task):
        """Runs every task inside the Flask app context, so db and config work in tasks.

        Flask-SQLAlchemy only works inside an app context. A web request gets one
        automatically, but a Celery task runs outside any request, so we open one here.
        """

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(
        app.name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
        task_cls=FlaskTask,  # every task uses the class above
    )

    # Without this, beat would read the schedule times as UTC instead of Indian time
    celery.conf.timezone = "Asia/Kolkata"
    # Report "STARTED" while a task is running, so the status route can tell
    # "waiting in the queue" apart from "being worked on"
    celery.conf.task_track_started = True

    # Celery beat reads this table and puts each task on the queue when its time comes.
    # Beat only sends the message; the worker is what actually runs the task.
    celery.conf.beat_schedule = {
        "daily-trek-reminders": {
            "task": "tasks.send_daily_reminders",
            # Once a day at REMINDER_HOUR:REMINDER_MINUTE (default 08:00)
            "schedule": pick_schedule(
                app,
                crontab(hour=app.config["REMINDER_HOUR"], minute=app.config["REMINDER_MINUTE"]),
            ),
        },
        "monthly-admin-report": {
            "task": "tasks.send_monthly_report",
            # 09:00 on day 1 of every month, reporting on the month that just ended
            "schedule": pick_schedule(app, crontab(day_of_month=1, hour=9, minute=0)),
        },
    }

    # Tasks in tasks.py are written with @shared_task, which means "use the default
    # Celery app". This line makes ours the default.
    celery.set_default()
    app.extensions["celery"] = celery
    return celery
