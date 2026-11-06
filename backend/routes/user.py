"""Trekker routes: browse treks, book, cancel, booking history and profile.

Every route is protected with @role_required("trekker").
"""
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from models import Booking, Trek, User, db
from utils import error_response, get_current_user, role_required

user_bp = Blueprint("user", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Browse treks
# ---------------------------------------------------------------------------

@user_bp.route("/treks", methods=["GET"])
@role_required(User.ROLE_TREKKER)
def list_open_treks():
    """Open treks only. Optional filters (all can be combined):
    ?difficulty= &location= &min_duration= &max_duration= &q= (text search)
    """
    query = Trek.query.filter(Trek.status == "Open")

    difficulty = request.args.get("difficulty")
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)

    location = (request.args.get("location") or "").strip()
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    # type=int returns None for text like "abc"; we treat that as a bad request
    for param in ("min_duration", "max_duration"):
        raw = request.args.get(param)
        if raw not in (None, "") and request.args.get(param, type=int) is None:
            return error_response(f"{param} must be a whole number.", 400)
    min_duration = request.args.get("min_duration", type=int)
    max_duration = request.args.get("max_duration", type=int)
    if min_duration is not None:
        query = query.filter(Trek.duration_days >= min_duration)
    if max_duration is not None:
        query = query.filter(Trek.duration_days <= max_duration)
    if min_duration is not None and max_duration is not None and min_duration > max_duration:
        return error_response("min_duration cannot be greater than max_duration.", 400)

    text = (request.args.get("q") or "").strip()
    if text:
        pattern = f"%{text}%"
        query = query.filter(
            Trek.name.ilike(pattern) | Trek.location.ilike(pattern) | Trek.description.ilike(pattern)
        )

    treks = query.order_by(Trek.start_date).all()
    return jsonify([trek.to_dict() for trek in treks]), 200


@user_bp.route("/treks/<int:trek_id>", methods=["GET"])
@role_required(User.ROLE_TREKKER)
def trek_detail(trek_id):
    """One trek's details, plus whether the logged-in trekker already has it booked."""
    user = get_current_user()

    trek = db.session.get(Trek, trek_id)
    if trek is None:
        return error_response("Trek not found.", 404)

    # Treks that are not Open are hidden from browsing, so only a trekker who has
    # (or had) a booking on one may open its page, e.g. from their booking history
    ever_booked = Booking.query.filter_by(user_id=user.id, trek_id=trek.id).first() is not None
    if trek.status != "Open" and not ever_booked:
        return error_response("Trek not found.", 404)

    already_booked = Booking.query.filter_by(user_id=user.id, trek_id=trek.id, status="Booked").first() is not None

    data = trek.to_dict()
    data["already_booked"] = already_booked  # lets the page disable the Book button
    return jsonify(data), 200


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------

@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@role_required(User.ROLE_TREKKER)
def book_trek(trek_id):
    """Book one seat on a trek."""
    user = get_current_user()

    trek = db.session.get(Trek, trek_id)
    if trek is None:
        return error_response("Trek not found.", 404)

    # --- Friendly checks (give clear messages in the normal case) ---
    if trek.status != "Open":
        return error_response("This trek is not open for booking.", 409)
    if trek.start_date and trek.start_date <= date.today():
        return error_response("This trek has already started or its start date has passed.", 409)

    # Duplicate check comes before the "full" check so a trekker who already holds
    # the last seat is told "you already booked", not "full"
    already_booked = Booking.query.filter_by(user_id=user.id, trek_id=trek.id, status="Booked").first()
    if already_booked:
        return error_response("You already have an active booking for this trek.", 409)
    if trek.available_slots <= 0:
        return error_response("This trek is full.", 409)

    # --- The real protection against two people taking the last slot ---
    # One UPDATE statement checks "slots > 0 and still Open" AND subtracts 1 together.
    # The database runs it as a single step, so if two requests race for the last seat,
    # the second one finds 0 slots, matches 0 rows, and is rejected.
    # (Reading the number in Python, then writing number-1, would NOT be safe.)
    rows_changed = Trek.query.filter(
        Trek.id == trek.id, Trek.status == "Open", Trek.available_slots > 0
    ).update({Trek.available_slots: Trek.available_slots - 1}, synchronize_session=False)

    if rows_changed == 0:
        db.session.rollback()
        return error_response("Sorry, the last slot was just taken.", 409)

    booking = Booking(user_id=user.id, trek_id=trek.id, status="Booked", payment_status="Pending")
    db.session.add(booking)

    # Slot decrease and new booking are saved in ONE commit (same transaction).
    # If the partial unique index on (user, trek) fires, e.g. a double-click sent
    # two requests at once, everything is rolled back, so no slot is lost.
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("You already have an active booking for this trek.", 409)

    db.session.refresh(trek)
    return jsonify({
        "message": f"Booked {trek.name}.",
        "booking": booking_details(booking),
        "available_slots": trek.available_slots,
    }), 201


@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["PUT"])
@role_required(User.ROLE_TREKKER)
def cancel_booking(booking_id):
    """Cancel my own booking before the trek starts, and give the slot back."""
    user = get_current_user()

    booking = db.session.get(Booking, booking_id)
    # Same 404 for "does not exist" and "belongs to someone else",
    # so a trekker cannot discover other people's booking ids.
    if booking is None or booking.user_id != user.id:
        return error_response("Booking not found.", 404)

    if booking.status != "Booked":
        return error_response(f"This booking is already {booking.status}.", 409)

    trek = booking.trek
    # The trek has started if staff marked it Ongoing/Completed or its start date has arrived
    if trek.status in ("Ongoing", "Completed") or (trek.start_date and trek.start_date <= date.today()):
        return error_response("The trek has already started, so it can no longer be cancelled.", 409)

    booking.status = "Cancelled"
    # Add 1 inside the database (not read-then-write) so it stays correct
    # if a booking or another cancellation happens at the same moment.
    Trek.query.filter(Trek.id == trek.id).update(
        {Trek.available_slots: Trek.available_slots + 1}, synchronize_session=False
    )
    db.session.commit()  # status change and slot give-back saved together

    return jsonify({"message": "Booking cancelled.", "booking": booking_details(booking)}), 200


def booking_details(booking):
    """Booking info plus the trek details a trekker wants to see."""
    data = booking.to_dict()
    trek = booking.trek
    data["trek_location"] = trek.location
    data["trek_status"] = trek.status
    data["start_date"] = trek.start_date.isoformat() if trek.start_date else None
    data["end_date"] = trek.end_date.isoformat() if trek.end_date else None
    data["price"] = trek.price
    return data


@user_bp.route("/bookings/me", methods=["GET"])
@role_required(User.ROLE_TREKKER)
def my_bookings():
    """My full booking history (Booked, Completed and Cancelled), newest first."""
    user = get_current_user()
    bookings = (
        Booking.query.filter_by(user_id=user.id)
        .order_by(Booking.booking_date.desc(), Booking.id.desc())  # id breaks ties
        .all()
    )
    return jsonify([booking_details(b) for b in bookings]), 200


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@user_bp.route("/profile", methods=["GET"])
@role_required(User.ROLE_TREKKER)
def get_profile():
    """Return my profile."""
    return jsonify(get_current_user().to_dict()), 200


@user_bp.route("/profile", methods=["PUT"])
@role_required(User.ROLE_TREKKER)
def update_profile():
    """Update my name and/or phone. Email, role and flags can't be changed here."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = (data["name"] or "").strip() if isinstance(data["name"], str) else ""
        if not name:
            return error_response("Name cannot be empty.", 400)
        user.name = name

    if "phone" in data:
        phone = (data["phone"] or "").strip() if isinstance(data["phone"], (str, type(None))) else None
        if phone is None:
            return error_response("Phone must be text.", 400)
        if len(phone) > 20:
            return error_response("Phone must be at most 20 characters.", 400)
        user.phone = phone

    db.session.commit()
    return jsonify({"message": "Profile updated.", "user": user.to_dict()}), 200
