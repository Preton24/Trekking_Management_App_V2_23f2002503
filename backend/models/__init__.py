# Shared SQLAlchemy object.
# It is created here (without an app) and connected to the Flask app
# later inside create_app() using db.init_app(app).
# Model files will import it with:  from models import db
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import every model AFTER db is defined (each model file does "from models import db").
# Importing them here means db.create_all() knows about all the tables, and other
# code can simply write:  from models import User, Trek, ...
from models.user import User  # noqa: E402
from models.staff_profile import StaffProfile  # noqa: E402
from models.trek import Trek  # noqa: E402
from models.booking import Booking  # noqa: E402
