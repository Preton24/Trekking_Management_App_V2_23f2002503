from datetime import datetime

from models import db


class Trek(db.Model):
    """A trek that trekkers can book, led by one assigned staff member."""

    __tablename__ = "treks"

    # Allowed values, kept here so routes can reuse them for validation
    DIFFICULTIES = ["Easy", "Moderate", "Hard"]
    STATUSES = ["Pending", "Approved", "Open", "Closed", "Completed"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    # Decreased on each booking and increased on cancellation, so we can
    # show free seats without counting bookings every time
    available_slots = db.Column(db.Integer, nullable=False)
    # Nullable: a new trek may not have a staff member assigned yet
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Many-to-one: many treks can be led by the same staff user
    assigned_staff = db.relationship("User", back_populates="assigned_treks")
    # One-to-many: a trek has many bookings
    bookings = db.relationship("Booking", back_populates="trek", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "description": self.description,
            "difficulty": self.difficulty,
            "duration_days": self.duration_days,
            "total_slots": self.total_slots,
            "available_slots": self.available_slots,
            "assigned_staff_id": self.assigned_staff_id,
            "assigned_staff_name": self.assigned_staff.name if self.assigned_staff else None,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "price": self.price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
