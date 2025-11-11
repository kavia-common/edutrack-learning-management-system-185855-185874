from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from ..models import User, Course, Enrollment, Submission
from ..security import require_roles

blp = Blueprint(
    "Analytics",
    "analytics",
    url_prefix="/api/analytics",
    description="Basic analytics endpoints",
)


@blp.route("/summary")
class Summary(MethodView):
    """
    PUBLIC_INTERFACE
    Get a summary of key metrics (admin/instructor).
    """
    @jwt_required()
    @require_roles(["admin", "instructor"])
    def get(self):
        return {
            "users": User.query.count(),
            "courses": Course.query.count(),
            "enrollments": Enrollment.query.count(),
            "quiz_submissions": Submission.query.count(),
        }
