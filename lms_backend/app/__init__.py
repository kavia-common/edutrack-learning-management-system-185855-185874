import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

# Initialize extensions (to be bound in create_app)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")  # Flask-SocketIO

# Blueprints imports (routes)
# Note: Imports inside create_app to avoid circulars on extensions


class Config:
    """Base configuration using environment variables. Do not hardcode secrets."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-env")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    TESTING = os.getenv("FLASK_TESTING", "0") == "1"

    # SQLAlchemy connection string; must be provided via env.
    # Example: mysql+pymysql://user:password@host:3306/dbname
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///lms_dev.sqlite")
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

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Certificates
    CERTIFICATE_ISSUER = os.getenv("CERTIFICATE_ISSUER", "EduTrack")
    SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")

    # Uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB


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
    socketio.init_app(app)

    # Initialize API
    api = Api(app)

    # Import models so Alembic/Migrate can discover them
    from .models import (  # noqa: F401
        User, Role, Course, Lesson, Resource, Quiz, Question, Enrollment,
        Progress, Submission, Notification, Payment, AuditLog, QuizOption
    )

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
