"""Authentication routes: trekker signup, login for all roles, and current-user profile.

There is deliberately NO route to register an admin or staff member:
the admin is seeded in code, and staff accounts are created by the admin.
"""
import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from models import User, db
from utils import error_response, get_current_user, role_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Simple email check: something@something.something (no spaces).
# Good enough to catch typos; real verification would need a confirmation email.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new TREKKER account. The role is always set here, never taken from the request."""
    # silent=True returns None instead of raising if the body is not valid JSON
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()  # lower-case so emails compare reliably
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()

    # --- 400: validate the input ---
    if not name or not email or not password:
        return error_response("Name, email and password are required.", 400)
    if not EMAIL_PATTERN.match(email):
        return error_response("Please enter a valid email address.", 400)
    if len(password) < MIN_PASSWORD_LENGTH:
        return error_response(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", 400)

    # --- 409: email must not already be used ---
    if User.query.filter_by(email=email).first():
        return error_response("An account with this email already exists.", 409)

    # role is hard-coded to trekker, so nobody can sign up as admin or staff
    user = User(name=name, email=email, phone=phone, role=User.ROLE_TREKKER)
    user.set_password(password)  # hashed with werkzeug's generate_password_hash
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful. Please log in.", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Check email + password for any role and return a signed JWT."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return error_response("Email and password are required.", 400)

    # --- 401: same message for unknown email and wrong password,
    # so an attacker cannot find out which emails are registered ---
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return error_response("Invalid email or password.", 401)

    # --- 403: correct password, but the admin has blocked this account ---
    if user.is_blacklisted:
        return error_response("Your account has been blacklisted. Contact the admin.", 403)
    if not user.is_active:
        return error_response("Your account is inactive. Contact the admin.", 403)

    # identity becomes the token's "sub" claim (must be a string in Flask-JWT-Extended 4.x).
    # The role goes in as an extra claim so role_required can check it without a lookup.
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    return jsonify({
        "access_token": access_token,
        "name": user.name,
        "role": user.role,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@role_required(User.ROLE_ADMIN, User.ROLE_STAFF, User.ROLE_TREKKER)
def me():
    """Return the logged-in user's profile (any role)."""
    user = get_current_user()
    profile = user.to_dict()

    # Staff also get their staff-specific details
    if user.role == User.ROLE_STAFF and user.staff_profile:
        profile["staff_profile"] = user.staff_profile.to_dict()

    return jsonify(profile), 200
