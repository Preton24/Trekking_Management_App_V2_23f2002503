"""Small helpers shared by all route files."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from models import User, db


def error_response(message, status_code):
    """Every error in the API uses this same JSON shape: {"error": "..."}."""
    return jsonify({"error": message}), status_code


def get_current_user():
    """Load the logged-in user from the database using the id stored in the JWT."""
    user_id = get_jwt_identity()  # the "sub" claim; we stored the user id as a string
    return db.session.get(User, int(user_id))


def role_required(*roles):
    """Decorator that lets a route run only for logged-in users with one of the given roles.

    Usage:
        @bp.route("/admin/stats")
        @role_required("admin")
        def stats(): ...

    Steps on every request:
      1. verify_jwt_in_request() checks the Authorization header has a valid,
         unexpired token signed with our secret key (otherwise -> 401).
      2. The role is read from the token's claims and compared with the allowed roles (-> 403).
      3. The user is loaded from the database, so an account that was deactivated or
         blacklisted AFTER logging in is blocked straight away, even though its token
         has not expired yet (-> 403).
    """

    def decorator(route_function):
        @wraps(route_function)  # keeps the original function name, which Flask needs for routing
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            role = get_jwt().get("role")
            if role not in roles:
                return error_response("You do not have permission to access this resource.", 403)

            user = get_current_user()
            if user is None:
                return error_response("User account no longer exists.", 401)
            if user.is_blacklisted:
                return error_response("Your account has been blacklisted. Contact the admin.", 403)
            if not user.is_active:
                return error_response("Your account is inactive. Contact the admin.", 403)

            return route_function(*args, **kwargs)

        return wrapper

    return decorator
