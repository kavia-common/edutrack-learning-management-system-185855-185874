from flask_smorest import Blueprint
from flask.views import MethodView

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
