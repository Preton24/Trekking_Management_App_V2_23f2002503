from datetime import datetime

from models import db


class Booking(db.Model):
    """A trekker's seat on a trek. Links one User to one Trek."""

    __tablename__ = "bookings"

    # Allowed values
    STATUSES = ["Booked", "Cancelled", "Completed"]
    PAYMENT_STATUSES = ["Pending", "Paid", "Refunded"]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default="Booked")
    payment_status = db.Column(db.String(20), nullable=False, default="Pending")

    # Block duplicate bookings at the database level.
    # This is a *partial* unique index: (user_id, trek_id) must be unique only
    # among rows where status = 'Booked'. A plain UniqueConstraint would also stop
    # a trekker from booking again after they cancelled, which we want to allow.
    # SQLite supports partial indexes, and SQLAlchemy creates it via sqlite_where.
    __table_args__ = (
        db.Index(
            "uq_active_booking_user_trek",
            "user_id",
            "trek_id",
            unique=True,
            sqlite_where=db.text("status = 'Booked'"),
        ),
    )

    user = db.relationship("User", back_populates="bookings")
    trek = db.relationship("Trek", back_populates="bookings")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "trek_id": self.trek_id,
            "trek_name": self.trek.name if self.trek else None,
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "status": self.status,
            "payment_status": self.payment_status,
        }
