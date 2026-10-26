from models import db


class StaffProfile(db.Model):
    """Extra details that only trek staff have.

    Kept in its own table so the users table does not fill up with
    columns that are empty for the admin and for every trekker.
    """

    __tablename__ = "staff_profiles"

    # Allowed values for the status column
    STATUS_ACTIVE = "Active"
    STATUS_INACTIVE = "Inactive"

    id = db.Column(db.Integer, primary_key=True)
    # unique=True makes this one-to-one: a user can have at most one staff profile
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    contact = db.Column(db.String(100))  # e.g. emergency / work contact
    experience = db.Column(db.Integer, default=0)  # years of trekking experience
    status = db.Column(db.String(20), nullable=False, default=STATUS_ACTIVE)

    user = db.relationship("User", back_populates="staff_profile")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact": self.contact,
            "experience": self.experience,
            "status": self.status,
        }
