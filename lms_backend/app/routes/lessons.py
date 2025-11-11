from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from ..models import Lesson
from .. import db
from ..security import require_roles

blp = Blueprint(
    "Lessons",
    "lessons",
    url_prefix="/api/lessons",
    description="Lesson management endpoints",
)


@blp.route("/course/<int:course_id>")
class LessonsByCourse(MethodView):
    """
    PUBLIC_INTERFACE
    List or create lessons under a course.
    """
    def get(self, course_id: int):
        lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.position).all()
        return [{"id": l.id, "title": l.title, "content": l.content, "video_url": l.video_url, "position": l.position} for l in lessons]

    @jwt_required()
    @require_roles(["instructor", "admin"])
    def post(self, course_id: int):
        data = request.get_json() or {}
        l = Lesson(
            course_id=course_id,
            title=data.get("title", "Untitled"),
            content=data.get("content"),
            video_url=data.get("video_url"),
            position=int(data.get("position", 0)),
        )
        db.session.add(l)
        db.session.commit()
        return {"id": l.id, "message": "Created"}, 201


@blp.route("/<int:lesson_id>")
class LessonDetail(MethodView):
    """
    PUBLIC_INTERFACE
    Get, update, or delete a lesson.
    """
    def get(self, lesson_id: int):
        l = Lesson.query.get_or_404(lesson_id)
        return {"id": l.id, "title": l.title, "content": l.content, "video_url": l.video_url, "position": l.position}

    @jwt_required()
    @require_roles(["instructor", "admin"])
    def put(self, lesson_id: int):
        l = Lesson.query.get_or_404(lesson_id)
        data = request.get_json() or {}
        l.title = data.get("title", l.title)
        l.content = data.get("content", l.content)
        l.video_url = data.get("video_url", l.video_url)
        l.position = int(data.get("position", l.position))
        db.session.commit()
        return {"message": "Updated"}

    @jwt_required()
    @require_roles(["instructor", "admin"])
    def delete(self, lesson_id: int):
        l = Lesson.query.get_or_404(lesson_id)
        db.session.delete(l)
        db.session.commit()
        return {"message": "Deleted"}
