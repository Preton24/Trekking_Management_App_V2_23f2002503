"""Trek staff routes. Every route is protected with @role_required("staff").

Staff can only see and change treks that the admin assigned to them.
"""
from flask import Blueprint, jsonify, request

from models import Booking, Trek, User, db
from utils import error_response, get_current_user, role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/api/staff")

# Booking statuses that still count as a registered participant (everything except Cancelled)
REGISTERED_STATUSES = ["Booked", "Completed"]


def is_whole_number(value):
    """True for real integers only. bool is excluded because True == 1 in Python."""
    return isinstance(value, int) and not isinstance(value, bool)


def count_registered(trek_id):
    """How many trekkers hold a seat on this trek (cancelled bookings are not counted)."""
    return Booking.query.filter(
        Booking.trek_id == trek_id, Booking.status.in_(REGISTERED_STATUSES)
    ).count()


def get_own_trek(trek_id):
    """Load a trek and check it belongs to the logged-in staff member.

    Returns (trek, error). If error is not None, the route should return it as-is:
    404 when the trek does not exist, 403 when it is assigned to someone else.
    """
    trek = db.session.get(Trek, trek_id)
    if trek is None:
        return None, error_response("Trek not found.", 404)

    staff = get_current_user()
    # This ownership check is what stops one staff member editing another's trek
    if trek.assigned_staff_id != staff.id:
        return None, error_response("This trek is not assigned to you.", 403)
    return trek, None


@staff_bp.route("/treks", methods=["GET"])
@role_required(User.ROLE_STAFF)
def my_treks():
    """List only the treks assigned to the logged-in staff member, with registered counts."""
    staff = get_current_user()
    treks = Trek.query.filter_by(assigned_staff_id=staff.id).order_by(Trek.start_date).all()

    result = []
    for trek in treks:
        data = trek.to_dict()
        data["registered_count"] = count_registered(trek.id)
        result.append(data)
    return jsonify(result), 200


@staff_bp.route("/treks/<int:trek_id>", methods=["PUT"])
@role_required(User.ROLE_STAFF)
def update_my_trek(trek_id):
    """Change a trek's slot capacity and/or open/close it.

    Body (both optional): {"total_slots": 25, "status": "Closed"}
    Staff cannot touch any other field (name, price, dates...); that is the admin's job.
    """
    trek, error = get_own_trek(trek_id)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    if "total_slots" not in data and "status" not in data:
        return error_response("Send total_slots and/or status to update.", 400)

    # A trek that is on the trail or finished can no longer be edited
    if trek.status in ("Ongoing", "Completed"):
        return error_response(f"A {trek.status} trek can no longer be changed.", 409)

    new_status = data.get("status", trek.status)
    new_total = data.get("total_slots", trek.total_slots)

    if "status" in data:
        if new_status not in ("Open", "Closed"):
            return error_response("Status must be Open or Closed.", 400)
        # Pending means the admin has not approved the trek yet, so staff cannot open it
        if trek.status == "Pending":
            return error_response("This trek is still Pending admin approval.", 409)

    booked = count_registered(trek.id)
    if "total_slots" in data:
        if not is_whole_number(new_total) or new_total <= 0:
            return error_response("Slots must be a whole number greater than 0.", 400)
        # Cannot take away seats that trekkers have already booked
        if new_total < booked:
            return error_response(
                f"Slots cannot be less than the {booked} seats already booked.", 400
            )

    trek.status = new_status
    trek.total_slots = new_total
    # Free seats = capacity minus seats already taken
    trek.available_slots = new_total - booked
    db.session.commit()

    result = trek.to_dict()
    result["registered_count"] = booked
    return jsonify({"message": "Trek updated.", "trek": result}), 200


@staff_bp.route("/treks/<int:trek_id>/participants", methods=["GET"])
@role_required(User.ROLE_STAFF)
def participants(trek_id):
    """List the trekkers registered on one of my treks (cancelled bookings are left out)."""
    trek, error = get_own_trek(trek_id)
    if error:
        return error

    bookings = (
        Booking.query.filter(Booking.trek_id == trek.id, Booking.status.in_(REGISTERED_STATUSES))
        .order_by(Booking.booking_date)
        .all()
    )

    people = []
    for booking in bookings:
        people.append({
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "name": booking.user.name,
            "email": booking.user.email,
            "phone": booking.user.phone,
            "booking_date": booking.booking_date.isoformat(),
            "status": booking.status,
            "payment_status": booking.payment_status,
        })
    return jsonify({"trek": trek.name, "count": len(people), "participants": people}), 200


@staff_bp.route("/treks/<int:trek_id>/start", methods=["PUT"])
@role_required(User.ROLE_STAFF)
def start_trek(trek_id):
    """Mark a trek as Ongoing. From now on trekkers can no longer cancel."""
    trek, error = get_own_trek(trek_id)
    if error:
        return error

    # Only a trek that was open for booking (and is now full or closed) can start
    if trek.status not in ("Open", "Closed"):
        return error_response(f"A {trek.status} trek cannot be started.", 409)

    trek.status = "Ongoing"
    db.session.commit()
    return jsonify({"message": "Trek started.", "trek": trek.to_dict()}), 200


@staff_bp.route("/treks/<int:trek_id>/complete", methods=["PUT"])
@role_required(User.ROLE_STAFF)
def complete_trek(trek_id):
    """Mark a trek Completed and mark all its active bookings Completed too."""
    trek, error = get_own_trek(trek_id)
    if error:
        return error

    # Must be started first, so a trek cannot be completed twice or skipped straight to done
    if trek.status != "Ongoing":
        return error_response("Only an Ongoing trek can be completed. Start it first.", 409)

    trek.status = "Completed"
    # Only 'Booked' rows change; Cancelled bookings stay Cancelled.
    # Both changes are saved in one commit, so they succeed or fail together.
    active_bookings = Booking.query.filter_by(trek_id=trek.id, status="Booked").all()
    for booking in active_bookings:
        booking.status = "Completed"
    db.session.commit()

    return jsonify({
        "message": f"Trek completed. {len(active_bookings)} bookings marked Completed.",
        "trek": trek.to_dict(),
    }), 200
