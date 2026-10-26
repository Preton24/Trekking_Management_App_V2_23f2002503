from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from models import db


class User(db.Model):
    """Every person who can log in: the admin, trek staff and trekkers.

    A simple 'role' text column is used instead of a separate Role table,
    because each user has exactly one role and there are only three of them.
    """

    __tablename__ = "users"

    # The three allowed values for the role column
    ROLE_ADMIN = "admin"
    ROLE_STAFF = "staff"
    ROLE_TREKKER = "trekker"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # used as the login id
    password_hash = db.Column(db.String(256), nullable=False)  # never store the plain password
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default=ROLE_TREKKER)
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # admin can deactivate an account
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)  # blocked by admin for misuse
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # One-to-one: a staff user has one StaffProfile (uselist=False gives an object, not a list)
    staff_profile = db.relationship(
        "StaffProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    # One-to-many: a staff user can be assigned to many treks
    assigned_treks = db.relationship("Trek", back_populates="assigned_staff")
    # One-to-many: a trekker can make many bookings
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash the password with Werkzeug (comes with Flask) and store only the hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert to a dictionary for JSON responses (password hash is left out on purpose)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "is_blacklisted": self.is_blacklisted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
