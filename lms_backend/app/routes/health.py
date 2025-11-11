from flask_smorest import Blueprint
from flask.views import MethodView
from sqlalchemy import text
from .. import db

blp = Blueprint(
    "Health",
    "health",
    url_prefix="/",
    description="Health check and root endpoint",
)


@blp.route("/")
class HealthCheck(MethodView):
    """Root health endpoint."""
    def get(self):
        return {"message": "Healthy"}


@blp.route("/health/db")
class HealthDB(MethodView):
    """
    PUBLIC_INTERFACE
    Database readiness endpoint. Returns 200 when DB is reachable.
    """
    def get(self):
        try:
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            return {"db": "ready"}
        except Exception as e:
            return {"db": "not_ready", "error": str(e)}, 503
