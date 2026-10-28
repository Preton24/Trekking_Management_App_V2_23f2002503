import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail

from models import User, db
from routes.admin import admin_bp
from routes.auth import auth_bp

# Folder that contains this file, used to build an absolute path for the SQLite file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """All app settings in one place. Values can be overridden with environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    # Used to sign JWTs; at least 32 characters so PyJWT does not warn about a weak key
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me-32-chars-long")
    # How long a login token stays valid. There are no refresh tokens, so after this
    # the user simply logs in again. 1 day keeps demos from logging out midway.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # SQLite database file stored inside backend/instance/
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis is used for caching (db 0) and for Celery (db 1 broker, db 2 results)
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # seconds
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # Mail settings (defaults suit a local test server such as MailHog on port 1025)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 1025))
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@trekking.local")

    # The single admin account, created in code on startup (there is no admin signup)
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "Admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trekking.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


# Extensions are created once here and attached to the app inside create_app()
cache = Cache()
jwt = JWTManager()
mail = Mail()


def seed_admin(app):
    """Create the one admin user from config, but only if no admin exists yet.

    Called on every startup, so the check stops a second admin being added
    each time the server restarts.
    """
    existing_admin = User.query.filter_by(role=User.ROLE_ADMIN).first()
    if existing_admin:
        return

    admin = User(
        name=app.config["ADMIN_NAME"],
        email=app.config["ADMIN_EMAIL"],
        role=User.ROLE_ADMIN,
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {admin.email}")


def create_app(config_class=Config):
    """App factory: builds and returns a configured Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Make sure the instance folder exists so SQLite can create the .db file there
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

    # Connect extensions to this app
    db.init_app(app)
    cache.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    # Allow the Vite dev server (a different port) to call /api/* routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Flask-JWT-Extended normally replies {"msg": ...} when a token is missing or bad.
    # These handlers make those errors use our {"error": ...} shape with status 401.
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Login required: missing access token."}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid access token. Please log in again."}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Your session has expired. Please log in again."}), 401

    # Register route blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Simple check that the server is running
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # Create all tables programmatically (never by hand), then make sure the admin exists
    with app.app_context():
        db.create_all()
        seed_admin(app)

    return app


if __name__ == "__main__":
    app = create_app()
    # Port 5001 because macOS AirPlay already uses port 5000
    app.run(port=5001, debug=True)
