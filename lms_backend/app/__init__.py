import os
import time
from datetime import timedelta
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from .env if present (non-fatal if missing)
load_dotenv()

# Initialize extensions (to be bound in create_app)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")  # Flask-SocketIO


class Config:
    """Base configuration using environment variables. Do not hardcode secrets."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-env")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    TESTING = os.getenv("FLASK_TESTING", "0") == "1"

    # SQLAlchemy connection string; prefer DATABASE_URL, else construct from components if provided
    # Example: mysql+pymysql://user:password@host:3306/dbname
    _db_url_env = os.getenv("DATABASE_URL")
    if not _db_url_env:
        db_user = os.getenv("DB_USER", os.getenv("MYSQL_USER"))
        db_pass = os.getenv("DB_PASSWORD", os.getenv("MYSQL_PASSWORD"))
        db_host = os.getenv("DB_HOST", os.getenv("MYSQL_HOST", "localhost"))
        db_port = os.getenv("DB_PORT", os.getenv("MYSQL_PORT", "3306"))
        db_name = os.getenv("DB_NAME", os.getenv("MYSQL_DB"))
        if db_user and db_pass and db_host and db_name:
            _db_url_env = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    SQLALCHEMY_DATABASE_URI = _db_url_env or "sqlite:///lms_dev.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-env")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_EXPIRES_SECONDS", str(60 * 60)))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_EXPIRES_SECONDS", str(60 * 60 * 24 * 30)))
    )

    # OpenAPI/Docs
    API_TITLE = "EduTrack LMS API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = ""
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Stripe (optional; should not block startup)
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Certificates
    CERTIFICATE_ISSUER = os.getenv("CERTIFICATE_ISSUER", "EduTrack")
    SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")

    # Uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

    # DB readiness wait configuration
    DB_READY_MAX_RETRIES = int(os.getenv("DB_READY_MAX_RETRIES", "30"))
    DB_READY_SLEEP_SECONDS = float(os.getenv("DB_READY_SLEEP_SECONDS", "2.0"))


def _wait_for_database(app: Flask) -> Optional[str]:
    """
    Wait for the database to be reachable using a simple SELECT 1; returns None on success, or error string.
    This avoids startup crashes when DB container is still initializing.
    """
    # If using SQLite local file/memory, no need to wait
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite:"):
        return None

    max_retries = app.config.get("DB_READY_MAX_RETRIES", 30)
    sleep_s = app.config.get("DB_READY_SLEEP_SECONDS", 2.0)

    last_err = None
    # Use a temporary engine via app.db engine after initialization
    for attempt in range(1, int(max_retries) + 1):
        try:
            with app.app_context():
                # Use a raw text query to avoid model imports here
                db.session.execute(text("SELECT 1"))
                db.session.commit()
            return None
        except Exception as e:
            last_err = str(e)
            time.sleep(float(sleep_s))
    return last_err


def create_app(config_object: type[Config] = Config) -> Flask:
    """
    PUBLIC_INTERFACE
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Bind extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    # Initialize socketio without blocking even if some async backends are missing
    try:
        socketio.init_app(app)
    except Exception:
        # Fallback: do not break app if Socket.IO cannot initialize in this environment
        pass

    # Initialize API
    api = Api(app)

    # Import models so Alembic/Migrate can discover them
    from .models import (  # noqa: F401
        User, Role, Course, Lesson, Resource, Quiz, Question, Enrollment,
        Progress, Submission, Notification, Payment, AuditLog, QuizOption
    )

    # Optionally wait for database readiness to avoid crashes on startup
    db_err = _wait_for_database(app)
    if db_err:
        # Do not crash; allow app to start so health endpoint can be polled while DB becomes ready.
        # Logging to stdout for visibility in container logs.
        print(f"[startup] Database not ready after retries: {db_err}")

    # Register blueprints
    from .routes.health import blp as health_blp
    from .routes.auth import blp as auth_blp
    from .routes.users import blp as users_blp
    from .routes.courses import blp as courses_blp
    from .routes.lessons import blp as lessons_blp
    from .routes.quizzes import blp as quizzes_blp
    from .routes.enrollments import blp as enrollments_blp
    from .routes.progress import blp as progress_blp
    from .routes.uploads import blp as uploads_blp
    from .routes.notifications import blp as notifications_blp
    from .routes.analytics import blp as analytics_blp
    from .routes.payments import blp as payments_blp
    from .routes.certificates import blp as certificates_blp
    from .routes.websocket_help import blp as ws_help_blp

    api.register_blueprint(health_blp)
    api.register_blueprint(ws_help_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(users_blp)
    api.register_blueprint(courses_blp)
    api.register_blueprint(lessons_blp)
    api.register_blueprint(quizzes_blp)
    api.register_blueprint(enrollments_blp)
    api.register_blueprint(progress_blp)
    api.register_blueprint(uploads_blp)
    api.register_blueprint(notifications_blp)
    api.register_blueprint(analytics_blp)
    api.register_blueprint(payments_blp)
    api.register_blueprint(certificates_blp)

    # JWT callbacks
    @jwt.invalid_token_loader
    def invalid_token_callback(reason: str):
        return jsonify({"message": "Invalid token", "reason": reason}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason: str):
        return jsonify({"message": "Missing token", "reason": reason}), 401

    return app


# Provide app and api variables for generate_openapi.py compatibility
app = create_app()
api = Api(app)

# Register Socket.IO namespaces when module-level app is created (useful for generate_openapi context or other scripts)
try:
    from .sockets import register_socket_namespaces
    register_socket_namespaces()
except Exception:
    # Avoid hard failures during tooling or docs generation
    pass
