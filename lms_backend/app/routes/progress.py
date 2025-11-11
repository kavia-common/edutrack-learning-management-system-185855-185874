from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Progress
from .. import db

blp = Blueprint(
    "Progress",
    "progress",
    url_prefix="/api/progress",
    description="Progress tracking endpoints",
)


@blp.route("/course/<int:course_id>")
class CourseProgress(MethodView):
    """
    PUBLIC_INTERFACE
    Get or update progress for a course.
    """
    @jwt_required()
    def get(self, course_id: int):
        ident = get_jwt_identity()
        p = Progress.query.filter_by(user_id=ident.get("id"), course_id=course_id).all()
        return [{"id": i.id, "lesson_id": i.lesson_id, "completed": i.completed, "updated_at": i.updated_at.isoformat()} for i in p]

    @jwt_required()
    def post(self, course_id: int):
        ident = get_jwt_identity()
        data = request.get_json() or {}
        lesson_id = data.get("lesson_id")
        completed = bool(data.get("completed", True))
        pr = Progress(user_id=ident.get("id"), course_id=course_id, lesson_id=lesson_id, completed=completed)
        db.session.add(pr)
        db.session.commit()
        return {"message": "Recorded", "id": pr.id}, 201
