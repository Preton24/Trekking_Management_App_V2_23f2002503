"""Background tasks run by the Celery worker.

Why these are Celery tasks and not normal route code: they are slow (network
calls, emails, writing files) and some must run on a timetable even when nobody
has the website open. The worker runs them in a separate process, so the Flask
API never makes a user wait for them.

@shared_task is used instead of importing the Celery object, so this file does
not import app.py. That lets the route files import tasks from here safely.
"""
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

from celery import shared_task
from flask import current_app, render_template
from flask_mail import Message
from fpdf import FPDF
from sqlalchemy import func

from models import Booking, Trek, User, db

# A reminder goes out when the trek starts within this many days from today
REMINDER_DAYS_AHEAD = 2

# The same general instructions are sent with every reminder
TREK_INSTRUCTIONS = (
    "Carry a valid photo ID, at least 2 litres of water, a rain jacket and "
    "comfortable trekking shoes. Reach the starting point 30 minutes early."
)

# Booking statuses that count as a participant (everything except Cancelled)
PARTICIPANT_STATUSES = ["Booked", "Completed"]

# Skip the Mac's system proxy lookup. On macOS that lookup can crash a Celery
# worker process, and a direct connection is all we need for the webhook.
no_proxy_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


# ---------------------------------------------------------------------------
# Google Chat helper (used by the reminders and the export alert)
# ---------------------------------------------------------------------------

def send_chat_message(webhook_url, text):
    """POST one text message to the Google Chat webhook. Returns True if it was accepted."""
    # A Google Chat webhook expects a JSON body of the form {"text": "..."}
    body = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,  # giving data makes this a POST request
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )
    try:
        # The timeout stops one slow call from hanging the whole task
        with no_proxy_opener.open(request, timeout=10) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError) as error:
        current_app.logger.error("Google Chat message failed: %s", error)
        return False


# ---------------------------------------------------------------------------
# 1. Daily reminders (scheduled by Celery beat)
# ---------------------------------------------------------------------------

def build_reminder_text(booking):
    """The message for one booking: trekker name, trek name, start date, location, instructions."""
    trek = booking.trek
    return (
        f"*Trek reminder for {booking.user.name}*\n"
        f"Trek: {trek.name}\n"
        f"Starts on: {trek.start_date.strftime('%d %b %Y')}\n"
        f"Location: {trek.location}\n"
        f"Instructions: {TREK_INSTRUCTIONS}"
    )


@shared_task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    """Send a Google Chat reminder for every active booking on a trek that starts soon.

    "Soon" means tomorrow up to REMINDER_DAYS_AHEAD days from today. The job runs
    once a day, so a trekker is reminded 2 days before and again 1 day before.
    """
    webhook_url = current_app.config["GOOGLE_CHAT_WEBHOOK_URL"]
    if not webhook_url:
        return "Skipped: GOOGLE_CHAT_WEBHOOK_URL is not set in .env."

    today = date.today()
    first_day = today + timedelta(days=1)
    last_day = today + timedelta(days=REMINDER_DAYS_AHEAD)

    # Only bookings that still hold a seat ("Booked"); cancelled ones get no reminder.
    # The join lets us filter bookings by a column of their trek (start_date).
    bookings = (
        Booking.query.join(Trek)
        .filter(
            Booking.status == "Booked",
            Trek.start_date >= first_day,
            Trek.start_date <= last_day,
        )
        .order_by(Trek.start_date)
        .all()
    )

    sent = 0
    failed = 0
    for booking in bookings:
        if send_chat_message(webhook_url, build_reminder_text(booking)):
            sent += 1
        else:
            failed += 1
        # Google Chat accepts about 1 webhook message per second for a space
        time.sleep(1)

    # The return value is stored in Redis (the result backend) and shown in the worker log
    return f"Daily reminders: {sent} sent, {failed} failed, for treks starting {first_day} to {last_day}."


# ---------------------------------------------------------------------------
# 2. Monthly report (scheduled by Celery beat on day 1 of every month)
# ---------------------------------------------------------------------------

def last_month_range(today):
    """Return (first day, last day) of the month before `today`."""
    first_of_this_month = today.replace(day=1)
    last_day = first_of_this_month - timedelta(days=1)  # one day back lands in last month
    first_day = last_day.replace(day=1)
    return first_day, last_day


def collect_monthly_report(first_day, last_day):
    """Gather the numbers for the report as plain lists and dicts (easy to show in a template)."""
    # "Conducted" = the trek started in that month and staff actually ran it.
    # Treks that stayed Pending/Open/Closed never went out, so they are left out.
    conducted_treks = (
        Trek.query.filter(
            Trek.start_date >= first_day,
            Trek.start_date <= last_day,
            Trek.status.in_(["Ongoing", "Completed"]),
        )
        .order_by(Trek.start_date)
        .all()
    )

    trek_rows = []
    total_participants = 0
    for trek in conducted_treks:
        participants = Booking.query.filter(
            Booking.trek_id == trek.id, Booking.status.in_(PARTICIPANT_STATUSES)
        ).count()
        total_participants += participants
        trek_rows.append({
            "name": trek.name,
            "location": trek.location,
            "start_date": trek.start_date.strftime("%d %b %Y"),
            "status": trek.status,
            "participants": participants,
        })

    # "Popular" = most bookings MADE during the month (cancelled ones not counted),
    # for any trek, including ones that have not started yet.
    # booking_date holds a date and a time, so the range runs from midnight on the
    # first day up to (but not including) midnight on the day after the last day.
    range_start = datetime.combine(first_day, datetime.min.time())
    range_end = datetime.combine(last_day + timedelta(days=1), datetime.min.time())
    booking_count = func.count(Booking.id)
    top_rows = (
        db.session.query(Trek.name, Trek.location, booking_count)
        .join(Booking, Booking.trek_id == Trek.id)
        .filter(
            Booking.status != "Cancelled",
            Booking.booking_date >= range_start,
            Booking.booking_date < range_end,
        )
        .group_by(Trek.id)
        .order_by(booking_count.desc(), Trek.name)
        .limit(3)
        .all()
    )
    top_treks = []
    for name, location, count in top_rows:
        top_treks.append({"name": name, "location": location, "bookings": count})

    return {
        "treks": trek_rows,
        "total_participants": total_participants,
        "top_treks": top_treks,
    }


def pdf_safe(text):
    """Swap characters the PDF's built-in font cannot draw for a "?".

    The standard PDF fonts (Helvetica) only cover Western European letters.
    Without this, one trek name containing e.g. a rupee sign or Tamil text
    would raise an error and no report would be sent at all.
    """
    return str(text).encode("latin-1", "replace").decode("latin-1")


def build_report_pdf(month_name, report):
    """Draw the same report as the email into a one-page PDF and return it as bytes.

    The PDF is built in memory (never saved to disk) because it is only needed
    as an email attachment.
    """
    pdf = FPDF()  # A4 page, measurements in millimetres
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Monthly activity report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, pdf_safe(month_name), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Summary numbers
    pdf.cell(0, 7, f"Treks conducted: {len(report['treks'])}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Participants: {report['total_participants']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Table 1: treks conducted
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, pdf_safe(f"Treks conducted in {month_name}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report["treks"]:
        # pdf.table() draws the borders and makes the first row a bold header.
        # col_widths are relative sizes, not millimetres.
        with pdf.table(col_widths=(30, 25, 18, 15, 15)) as table:
            header = table.row()
            for title in ["Trek", "Location", "Started", "Status", "Participants"]:
                header.cell(title)
            for trek in report["treks"]:
                row = table.row()
                row.cell(pdf_safe(trek["name"]))
                row.cell(pdf_safe(trek["location"]))
                row.cell(trek["start_date"])
                row.cell(trek["status"])
                row.cell(str(trek["participants"]))
    else:
        pdf.cell(0, 7, pdf_safe(f"No treks were conducted in {month_name}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Table 2: top 3 popular treks
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, "Top 3 popular treks (by bookings made)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report["top_treks"]:
        with pdf.table(col_widths=(8, 40, 35, 15)) as table:
            header = table.row()
            for title in ["#", "Trek", "Location", "Bookings"]:
                header.cell(title)
            position = 1
            for trek in report["top_treks"]:
                row = table.row()
                row.cell(str(position))
                row.cell(pdf_safe(trek["name"]))
                row.cell(pdf_safe(trek["location"]))
                row.cell(str(trek["bookings"]))
                position += 1
    else:
        pdf.cell(0, 7, pdf_safe(f"No bookings were made in {month_name}."), new_x="LMARGIN", new_y="NEXT")

    # output() with no file name returns the finished PDF as bytes
    return bytes(pdf.output())


@shared_task(name="tasks.send_monthly_report")
def send_monthly_report():
    """Email the admin last month's activity: an HTML body plus the same report as a PDF."""
    first_day, last_day = last_month_range(date.today())
    month_name = first_day.strftime("%B %Y")  # e.g. "October 2026"

    # Send to MONTHLY_REPORT_EMAIL if it is set, otherwise to the admin account's email
    recipient = current_app.config["MONTHLY_REPORT_EMAIL"]
    if not recipient:
        admin = User.query.filter_by(role=User.ROLE_ADMIN).first()
        recipient = admin.email

    report = collect_monthly_report(first_day, last_day)

    # The HTML is built from a Jinja template (backend/templates/monthly_report.html)
    html = render_template("monthly_report.html", month_name=month_name, report=report)

    message = Message(
        subject=f"Trekking monthly report: {month_name}",
        recipients=[recipient],
        html=html,
    )
    # The same numbers again as a PDF attachment, which is easier to save or print
    pdf_bytes = build_report_pdf(month_name, report)
    pdf_filename = "trekking_report_" + first_day.strftime("%Y_%m") + ".pdf"  # e.g. trekking_report_2026_10.pdf
    message.attach(pdf_filename, "application/pdf", pdf_bytes)

    # Flask-Mail stores itself in app.extensions when mail.init_app(app) runs.
    # Reading it from there avoids importing app.py into this file.
    # The Gmail address and app password come from .env through the app config.
    current_app.extensions["mail"].send(message)

    return (
        f"Monthly report for {month_name} sent to {recipient}: "
        f"{len(report['treks'])} treks conducted, {report['total_participants']} participants."
    )


# ---------------------------------------------------------------------------
# 3. CSV export (started by a user through POST /api/bookings/export)
# ---------------------------------------------------------------------------

@shared_task(name="tasks.export_bookings_csv", bind=True)
def export_bookings_csv(self, user_id):
    """Write one trekker's bookings to a CSV file in static/exports/.

    This is async because building a file can take a while when there are many
    rows; the user gets a task id straight away and the page checks on it.
    bind=True gives the task `self`, which we need to read this task's own id.
    """
    user = db.session.get(User, user_id)
    bookings = (
        Booking.query.filter_by(user_id=user_id)
        .order_by(Booking.booking_date.desc(), Booking.id.desc())
        .all()
    )

    # Flask serves files in backend/static/ at /static/..., so the browser can download from here
    export_folder = os.path.join(current_app.static_folder, "exports")
    os.makedirs(export_folder, exist_ok=True)

    # The task id is a long random value, so the file name cannot be guessed by
    # another user, and two exports never overwrite each other.
    filename = f"bookings_{self.request.id}.csv"
    file_path = os.path.join(export_folder, filename)

    # newline="" is what the csv module asks for, so rows are not double-spaced on Windows
    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "User ID", "Trek Name", "Location", "Booking Status",
            "Booking Date", "Trek Start Date", "Trek End Date",
        ])
        for booking in bookings:
            trek = booking.trek
            writer.writerow([
                booking.user_id,
                trek.name,
                trek.location,
                booking.status,
                booking.booking_date.strftime("%Y-%m-%d %H:%M"),
                trek.start_date.isoformat() if trek.start_date else "",
                trek.end_date.isoformat() if trek.end_date else "",
            ])

    # Tell the Google Chat space that the export is ready
    webhook_url = current_app.config["GOOGLE_CHAT_WEBHOOK_URL"]
    if webhook_url:
        send_chat_message(
            webhook_url,
            f"*Booking export ready*\n{user.name}'s CSV export has finished: {len(bookings)} booking(s).",
        )

    # This dict is saved in Redis as the task's result. GET /api/tasks/<id> reads it
    # to build the download link, and uses user_id to check who owns the export.
    return {"user_id": user_id, "filename": filename, "rows": len(bookings)}
