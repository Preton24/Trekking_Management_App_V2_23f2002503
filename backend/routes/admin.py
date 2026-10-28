"""Admin-only routes. Every route here is protected with @role_required("admin").

The role check runs on the backend for every route, so hiding a button in the
frontend is only for looks; it is not what keeps these routes safe.
"""
import re
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from models import Booking, StaffProfile, Trek, User, db
from utils import error_response, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# Same simple email check and minimum password length as the signup route
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def parse_date(text):
    """Turn 'YYYY-MM-DD' into a date. Returns None if the text is not a valid date."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def is_whole_number(value):
    """True for real integers only. bool is excluded because True == 1 in Python."""
    return isinstance(value, int) and not isinstance(value, bool)


def count_booked_seats(trek_id):
    """Seats currently held on a trek (bookings with status 'Booked')."""
    return Booking.query.filter_by(trek_id=trek_id, status="Booked").count()


def get_staff_user(staff_id):
    """Return the staff User with this id, or None if it does not exist or is not staff."""
    user = db.session.get(User, staff_id)
    if user is None or user.role != User.ROLE_STAFF:
        return None
    return user


def staff_to_dict(user):
    """User details plus the staff profile, in one dictionary."""
    data = user.to_dict()
    data["staff_profile"] = user.staff_profile.to_dict() if user.staff_profile else None
    return data


# ---------------------------------------------------------------------------
# Treks
# ---------------------------------------------------------------------------

def validate_trek_fields(fields):
    """Check the full set of trek fields. Returns an error message, or None if all is fine.

    `fields` is a dict with name, location, difficulty, status, total_slots,
    price, start_date and end_date (dates already parsed to date objects or None).
    """
    if not fields["name"] or not fields["location"]:
        return "Trek name and location are required."
    if fields["difficulty"] not in Trek.DIFFICULTIES:
        return "Difficulty must be one of: " + ", ".join(Trek.DIFFICULTIES) + "."
    if fields["status"] not in Trek.STATUSES:
        return "Status must be one of: " + ", ".join(Trek.STATUSES) + "."

    if not is_whole_number(fields["total_slots"]) or fields["total_slots"] <= 0:
        return "Total slots must be a whole number greater than 0."

    price = fields["price"]
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        return "Price must be a number that is 0 or more."

    if fields["start_date"] is None or fields["end_date"] is None:
        return "Start date and end date are required, in YYYY-MM-DD format."
    if fields["end_date"] <= fields["start_date"]:
        return "End date must be after the start date."
    return None


@admin_bp.route("/treks", methods=["GET"])
@role_required(User.ROLE_ADMIN)
def list_treks():
    """List treks. Optional filters: ?status= &difficulty= &staff_id= &q= (name/location text)."""
    query = Trek.query

    status = request.args.get("status")
    if status:
        query = query.filter(Trek.status == status)

    difficulty = request.args.get("difficulty")
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)

    staff_id = request.args.get("staff_id", type=int)
    if staff_id:
        query = query.filter(Trek.assigned_staff_id == staff_id)

    text = (request.args.get("q") or "").strip()
    if text:
        pattern = f"%{text}%"
        query = query.filter(Trek.name.ilike(pattern) | Trek.location.ilike(pattern))

    treks = query.order_by(Trek.start_date).all()
    return jsonify([trek.to_dict() for trek in treks]), 200


@admin_bp.route("/treks", methods=["POST"])
@role_required(User.ROLE_ADMIN)
def create_trek():
    """Create a trek. Duration is worked out from the dates; all slots start free."""
    data = request.get_json(silent=True) or {}

    fields = {
        "name": (data.get("name") or "").strip(),
        "location": (data.get("location") or "").strip(),
        "difficulty": data.get("difficulty", "Easy"),
        "status": data.get("status", "Pending"),
        "total_slots": data.get("total_slots"),
        "price": data.get("price", 0),
        "start_date": parse_date(data.get("start_date")),
        "end_date": parse_date(data.get("end_date")),
    }
    message = validate_trek_fields(fields)
    if message:
        return error_response(message, 400)

    # Counting both the first and last day, a trek from the 5th to the 9th lasts 5 days
    duration_days = (fields["end_date"] - fields["start_date"]).days + 1

    trek = Trek(
        name=fields["name"],
        location=fields["location"],
        description=(data.get("description") or "").strip(),
        difficulty=fields["difficulty"],
        status=fields["status"],
        total_slots=fields["total_slots"],
        available_slots=fields["total_slots"],  # nobody has booked yet
        price=fields["price"],
        start_date=fields["start_date"],
        end_date=fields["end_date"],
        duration_days=duration_days,
    )
    db.session.add(trek)
    db.session.commit()
    return jsonify({"message": "Trek created.", "trek": trek.to_dict()}), 201


@admin_bp.route("/treks/<int:trek_id>", methods=["PUT"])
@role_required(User.ROLE_ADMIN)
def update_trek(trek_id):
    """Update a trek. Fields that are not sent keep their current value."""
    trek = db.session.get(Trek, trek_id)
    if trek is None:
        return error_response("Trek not found.", 404)

    data = request.get_json(silent=True) or {}

    # Start from the current values, then overwrite with whatever was sent.
    # Validating the merged result means the date check also works when
    # only one of the two dates is being changed.
    fields = {
        "name": (data["name"] or "").strip() if "name" in data else trek.name,
        "location": (data["location"] or "").strip() if "location" in data else trek.location,
        "difficulty": data.get("difficulty", trek.difficulty),
        "status": data.get("status", trek.status),
        "total_slots": data.get("total_slots", trek.total_slots),
        "price": data.get("price", trek.price),
        "start_date": parse_date(data["start_date"]) if "start_date" in data else trek.start_date,
        "end_date": parse_date(data["end_date"]) if "end_date" in data else trek.end_date,
    }
    message = validate_trek_fields(fields)
    if message:
        return error_response(message, 400)

    # Slots can't shrink below the seats that are already booked
    booked_seats = count_booked_seats(trek.id)
    if fields["total_slots"] < booked_seats:
        return error_response(
            f"Total slots cannot be less than the {booked_seats} seats already booked.", 400
        )

    trek.name = fields["name"]
    trek.location = fields["location"]
    if "description" in data:
        trek.description = (data["description"] or "").strip()
    trek.difficulty = fields["difficulty"]
    trek.status = fields["status"]
    trek.price = fields["price"]
    trek.start_date = fields["start_date"]
    trek.end_date = fields["end_date"]
    trek.duration_days = (trek.end_date - trek.start_date).days + 1
    trek.total_slots = fields["total_slots"]
    # Free seats = capacity minus seats already taken
    trek.available_slots = trek.total_slots - booked_seats

    db.session.commit()
    return jsonify({"message": "Trek updated.", "trek": trek.to_dict()}), 200


@admin_bp.route("/treks/<int:trek_id>", methods=["DELETE"])
@role_required(User.ROLE_ADMIN)
def delete_trek(trek_id):
    """Delete a trek that has no bookings.

    A trek with bookings is kept so the booking history is not lost;
    the admin can set its status to Closed instead.
    """
    trek = db.session.get(Trek, trek_id)
    if trek is None:
        return error_response("Trek not found.", 404)

    if Booking.query.filter_by(trek_id=trek.id).count() > 0:
        return error_response(
            "This trek has bookings and cannot be deleted. Set its status to Closed instead.", 409
        )

    db.session.delete(trek)
    db.session.commit()
    return jsonify({"message": "Trek deleted."}), 200


@admin_bp.route("/treks/<int:trek_id>/assign", methods=["PUT"])
@role_required(User.ROLE_ADMIN)
def assign_staff(trek_id):
    """Assign a staff member to a trek. Body: {"staff_id": 3}"""
    trek = db.session.get(Trek, trek_id)
    if trek is None:
        return error_response("Trek not found.", 404)

    data = request.get_json(silent=True) or {}
    staff_id = data.get("staff_id")
    if not is_whole_number(staff_id):
        return error_response("staff_id is required and must be a number.", 400)

    staff = get_staff_user(staff_id)
    if staff is None:
        return error_response("Staff member not found.", 404)

    # Don't hand a trek to someone who cannot log in or is marked inactive
    profile_inactive = staff.staff_profile and staff.staff_profile.status != StaffProfile.STATUS_ACTIVE
    if staff.is_blacklisted or not staff.is_active or profile_inactive:
        return error_response("This staff member is not active and cannot be assigned.", 400)

    trek.assigned_staff_id = staff.id
    db.session.commit()
    return jsonify({"message": f"{staff.name} assigned to {trek.name}.", "trek": trek.to_dict()}), 200


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

@admin_bp.route("/staff", methods=["GET"])
@role_required(User.ROLE_ADMIN)
def list_staff():
    """List all staff members with their staff profile."""
    staff_users = User.query.filter_by(role=User.ROLE_STAFF).order_by(User.name).all()
    return jsonify([staff_to_dict(user) for user in staff_users]), 200


@admin_bp.route("/staff", methods=["POST"])
@role_required(User.ROLE_ADMIN)
def create_staff():
    """Create a staff account (User with role 'staff') and its StaffProfile.

    Staff cannot sign themselves up, so the admin chooses their first password.
    """
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    contact = (data.get("contact") or "").strip()
    experience = data.get("experience", 0)

    if not name or not email or not password:
        return error_response("Name, email and password are required.", 400)
    if not EMAIL_PATTERN.match(email):
        return error_response("Please enter a valid email address.", 400)
    if len(password) < MIN_PASSWORD_LENGTH:
        return error_response(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", 400)
    if not is_whole_number(experience) or experience < 0:
        return error_response("Experience must be a whole number of years (0 or more).", 400)
    if User.query.filter_by(email=email).first():
        return error_response("An account with this email already exists.", 409)

    # The role is fixed here; it is never read from the request body
    user = User(name=name, email=email, phone=phone, role=User.ROLE_STAFF)
    user.set_password(password)
    user.staff_profile = StaffProfile(contact=contact, experience=experience)

    # One commit saves the user and the profile together, or neither
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Staff account created.", "staff": staff_to_dict(user)}), 201


@admin_bp.route("/staff/<int:staff_id>", methods=["PUT"])
@role_required(User.ROLE_ADMIN)
def update_staff(staff_id):
    """Update a staff member's details. Fields that are not sent stay unchanged."""
    user = get_staff_user(staff_id)
    if user is None:
        return error_response("Staff member not found.", 404)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return error_response("Name cannot be empty.", 400)
        user.name = name

    if "email" in data:
        email = (data["email"] or "").strip().lower()
        if not EMAIL_PATTERN.match(email):
            return error_response("Please enter a valid email address.", 400)
        # Another account may already use this email (this user's own email is fine)
        other = User.query.filter(User.email == email, User.id != user.id).first()
        if other:
            return error_response("An account with this email already exists.", 409)
        user.email = email

    if "phone" in data:
        user.phone = (data["phone"] or "").strip()

    if "password" in data:
        if len(data["password"] or "") < MIN_PASSWORD_LENGTH:
            return error_response(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", 400)
        user.set_password(data["password"])

    # Staff profile fields. Create the profile if (unexpectedly) it is missing.
    profile = user.staff_profile
    if profile is None:
        profile = StaffProfile()
        user.staff_profile = profile

    if "contact" in data:
        profile.contact = (data["contact"] or "").strip()
    if "experience" in data:
        if not is_whole_number(data["experience"]) or data["experience"] < 0:
            return error_response("Experience must be a whole number of years (0 or more).", 400)
        profile.experience = data["experience"]
    if "status" in data:
        if data["status"] not in (StaffProfile.STATUS_ACTIVE, StaffProfile.STATUS_INACTIVE):
            return error_response("Status must be Active or Inactive.", 400)
        profile.status = data["status"]

    db.session.commit()
    return jsonify({"message": "Staff updated.", "staff": staff_to_dict(user)}), 200


@admin_bp.route("/staff/<int:staff_id>", methods=["DELETE"])
@role_required(User.ROLE_ADMIN)
def delete_staff(staff_id):
    """Delete a staff account (the StaffProfile is removed with it).

    Blocked while the staff member still leads a trek, so no trek is left
    pointing at a user that no longer exists.
    """
    user = get_staff_user(staff_id)
    if user is None:
        return error_response("Staff member not found.", 404)

    if Trek.query.filter_by(assigned_staff_id=user.id).count() > 0:
        return error_response(
            "This staff member is assigned to treks. Assign those treks to someone else first.", 409
        )

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Staff account deleted."}), 200


# ---------------------------------------------------------------------------
# Users (trekkers and staff): list, blacklist, activate
# ---------------------------------------------------------------------------

@admin_bp.route("/users", methods=["GET"])
@role_required(User.ROLE_ADMIN)
def list_users():
    """List trekkers by default. Use ?role=staff for staff, or ?role=all for both.

    The admin account is never listed, so it can't be picked for blacklisting.
    """
    role = request.args.get("role", User.ROLE_TREKKER)
    query = User.query.filter(User.role != User.ROLE_ADMIN)

    if role in (User.ROLE_TREKKER, User.ROLE_STAFF):
        query = query.filter(User.role == role)
    elif role != "all":
        return error_response("role must be trekker, staff or all.", 400)

    users = query.order_by(User.name).all()
    return jsonify([user.to_dict() for user in users]), 200


@admin_bp.route("/users/<int:user_id>/blacklist", methods=["PUT"])
@role_required(User.ROLE_ADMIN)
def blacklist_user(user_id):
    """Blacklist a trekker or staff member.

    role_required checks the database on every request, so the person is
    blocked straight away even if they still hold a valid token.
    """
    user = db.session.get(User, user_id)
    if user is None:
        return error_response("User not found.", 404)

    # The admin must not be able to lock themselves out
    if user.role == User.ROLE_ADMIN:
        return error_response("The admin account cannot be blacklisted.", 400)

    user.is_blacklisted = True
    db.session.commit()
    return jsonify({"message": f"{user.name} has been blacklisted.", "user": user.to_dict()}), 200


@admin_bp.route("/users/<int:user_id>/activate", methods=["PUT"])
@role_required(User.ROLE_ADMIN)
def activate_user(user_id):
    """Undo a blacklist and make sure the account is active, so the person can log in again."""
    user = db.session.get(User, user_id)
    if user is None:
        return error_response("User not found.", 404)

    user.is_blacklisted = False
    user.is_active = True
    db.session.commit()
    return jsonify({"message": f"{user.name} has been activated.", "user": user.to_dict()}), 200


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

@admin_bp.route("/bookings", methods=["GET"])
@role_required(User.ROLE_ADMIN)
def list_bookings():
    """List all bookings. Optional filters: ?trek_id= &user_id= &status="""
    query = Booking.query

    trek_id = request.args.get("trek_id", type=int)
    if trek_id:
        query = query.filter(Booking.trek_id == trek_id)

    user_id = request.args.get("user_id", type=int)
    if user_id:
        query = query.filter(Booking.user_id == user_id)

    status = request.args.get("status")
    if status:
        if status not in Booking.STATUSES:
            return error_response("Status must be one of: " + ", ".join(Booking.STATUSES) + ".", 400)
        query = query.filter(Booking.status == status)

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return jsonify([booking.to_dict() for booking in bookings]), 200


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@admin_bp.route("/search", methods=["GET"])
@role_required(User.ROLE_ADMIN)
def search():
    """Search by text. ?q=<text>&type=users|staff|treks

    users/staff match name or email; treks match name or location.
    """
    text = (request.args.get("q") or "").strip()
    search_type = request.args.get("type")

    if not text:
        return error_response("Search text q is required.", 400)
    if search_type not in ("users", "staff", "treks"):
        return error_response("type must be users, staff or treks.", 400)

    pattern = f"%{text}%"  # ilike makes the match case-insensitive

    if search_type == "treks":
        treks = Trek.query.filter(Trek.name.ilike(pattern) | Trek.location.ilike(pattern)).all()
        return jsonify([trek.to_dict() for trek in treks]), 200

    # "users" means trekkers; "staff" means staff members
    role = User.ROLE_TREKKER if search_type == "users" else User.ROLE_STAFF
    people = User.query.filter(
        User.role == role,
        User.name.ilike(pattern) | User.email.ilike(pattern),
    ).all()

    if search_type == "staff":
        return jsonify([staff_to_dict(person) for person in people]), 200
    return jsonify([person.to_dict() for person in people]), 200


# ---------------------------------------------------------------------------
# Stats (numbers for the dashboard cards and ChartJS charts)
# ---------------------------------------------------------------------------

@admin_bp.route("/stats", methods=["GET"])
@role_required(User.ROLE_ADMIN)
def stats():
    """Totals plus two chart-ready lists.

    bookings_per_trek counts bookings that are not cancelled, because a
    cancelled seat is free again and should not make a trek look popular.
    Every trek appears (even with 0 bookings) and every status appears (even with 0).
    """
    # Count of bookings for each trek id, done in one query by the database
    counts = (
        db.session.query(Booking.trek_id, func.count(Booking.id))
        .filter(Booking.status != "Cancelled")
        .group_by(Booking.trek_id)
        .all()
    )
    booking_count_by_trek = {trek_id: count for trek_id, count in counts}

    bookings_per_trek = []
    for trek in Trek.query.order_by(Trek.name).all():
        bookings_per_trek.append({
            "trek_id": trek.id,
            "trek_name": trek.name,
            "bookings": booking_count_by_trek.get(trek.id, 0),
        })

    treks_by_status = []
    for status in Trek.STATUSES:
        treks_by_status.append({
            "status": status,
            "count": Trek.query.filter_by(status=status).count(),
        })

    return jsonify({
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role=User.ROLE_TREKKER).count(),
        "total_staff": User.query.filter_by(role=User.ROLE_STAFF).count(),
        "total_bookings": Booking.query.count(),
        "bookings_per_trek": bookings_per_trek,
        "treks_by_status": treks_by_status,
    }), 200
