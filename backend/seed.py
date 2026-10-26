"""Demo data: 2 staff, 3 trekkers and 5 treks.

Run from the backend/ folder:   python seed.py

Safe to run more than once: a user is skipped if their email already exists,
and a trek is skipped if a trek with the same name already exists.
The admin is NOT created here; create_app() already seeds the admin.
"""
from datetime import date

from app import create_app
from models import StaffProfile, Trek, User, db

# Every demo account uses this password so they are easy to log in with
DEMO_PASSWORD = "password123"

STAFF = [
    {"name": "Ravi Kumar", "email": "ravi@trekking.local", "phone": "9876500001",
     "contact": "Base camp office, Manali", "experience": 8},
    {"name": "Anita Sharma", "email": "anita@trekking.local", "phone": "9876500002",
     "contact": "Base camp office, Dehradun", "experience": 5},
]

TREKKERS = [
    {"name": "Arjun Mehta", "email": "arjun@example.com", "phone": "9000000001"},
    {"name": "Priya Nair", "email": "priya@example.com", "phone": "9000000002"},
    {"name": "Karthik Rao", "email": "karthik@example.com", "phone": "9000000003"},
]

# "staff_email" says which staff member leads the trek (None = not assigned yet)
TREKS = [
    {"name": "Hampta Pass", "location": "Himachal Pradesh", "difficulty": "Moderate",
     "duration_days": 5, "total_slots": 20, "price": 8500, "status": "Open",
     "start_date": date(2026, 12, 5), "end_date": date(2026, 12, 9),
     "description": "Crossover trek from the green Kullu valley to the desert-like Lahaul.",
     "staff_email": "ravi@trekking.local"},
    {"name": "Kedarkantha", "location": "Uttarakhand", "difficulty": "Easy",
     "duration_days": 6, "total_slots": 25, "price": 7500, "status": "Open",
     "start_date": date(2026, 12, 20), "end_date": date(2026, 12, 25),
     "description": "Popular winter trek with a summit view of Himalayan peaks.",
     "staff_email": "anita@trekking.local"},
    {"name": "Roopkund", "location": "Uttarakhand", "difficulty": "Hard",
     "duration_days": 8, "total_slots": 15, "price": 14000, "status": "Approved",
     "start_date": date(2027, 5, 10), "end_date": date(2027, 5, 17),
     "description": "High-altitude trek to the mysterious skeleton lake.",
     "staff_email": "anita@trekking.local"},
    {"name": "Valley of Flowers", "location": "Uttarakhand", "difficulty": "Moderate",
     "duration_days": 6, "total_slots": 30, "price": 9500, "status": "Pending",
     "start_date": date(2027, 7, 15), "end_date": date(2027, 7, 20),
     "description": "UNESCO heritage valley famous for its alpine flowers.",
     "staff_email": None},
    {"name": "Triund", "location": "Himachal Pradesh", "difficulty": "Easy",
     "duration_days": 2, "total_slots": 40, "price": 2500, "status": "Completed",
     "start_date": date(2026, 9, 12), "end_date": date(2026, 9, 13),
     "description": "Short weekend trek above McLeod Ganj with Dhauladhar views.",
     "staff_email": "ravi@trekking.local"},
]


def create_user(name, email, phone, role):
    """Create a user unless the email is already taken. Returns the user either way."""
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"  skip user (exists): {email}")
        return user

    user = User(name=name, email=email, phone=phone, role=role)
    user.set_password(DEMO_PASSWORD)
    db.session.add(user)
    print(f"  added {role}: {email}")
    return user


def seed():
    print("Seeding staff...")
    for staff in STAFF:
        user = create_user(staff["name"], staff["email"], staff["phone"], User.ROLE_STAFF)
        # Give each staff user a profile if they do not have one yet
        if user.staff_profile is None:
            user.staff_profile = StaffProfile(
                contact=staff["contact"], experience=staff["experience"]
            )

    print("Seeding trekkers...")
    for trekker in TREKKERS:
        create_user(trekker["name"], trekker["email"], trekker["phone"], User.ROLE_TREKKER)

    # Save users now so staff have ids we can assign to treks
    db.session.commit()

    print("Seeding treks...")
    for trek_data in TREKS:
        if Trek.query.filter_by(name=trek_data["name"]).first():
            print(f"  skip trek (exists): {trek_data['name']}")
            continue

        staff_user = None
        if trek_data["staff_email"]:
            staff_user = User.query.filter_by(email=trek_data["staff_email"]).first()

        trek = Trek(
            name=trek_data["name"],
            location=trek_data["location"],
            description=trek_data["description"],
            difficulty=trek_data["difficulty"],
            duration_days=trek_data["duration_days"],
            total_slots=trek_data["total_slots"],
            available_slots=trek_data["total_slots"],  # no bookings yet, so all slots free
            assigned_staff=staff_user,
            status=trek_data["status"],
            start_date=trek_data["start_date"],
            end_date=trek_data["end_date"],
            price=trek_data["price"],
        )
        db.session.add(trek)
        print(f"  added trek: {trek.name}")

    db.session.commit()
    print("Done.")


if __name__ == "__main__":
    app = create_app()  # this also runs db.create_all() and seeds the admin
    with app.app_context():
        seed()
