from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Enrollment


blp = Blueprint(
    "Enrollments",
    "enrollments",
    url_prefix="/api/enrollments",
    description="Enrollment listing for the current user",
)


@blp.route("/")
class MyEnrollments(MethodView):
    """
    PUBLIC_INTERFACE
    List current user's enrollments.
    """
    @jwt_required()
    def get(self):
        ident = get_jwt_identity()
        enrollments = Enrollment.query.filter_by(user_id=ident.get("id")).all()
        return [{"id": e.id, "course_id": e.course_id, "status": e.status, "enrolled_at": e.enrolled_at.isoformat()} for e in enrollments]
