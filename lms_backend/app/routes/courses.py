from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Course
from .. import db
from ..security import require_roles
from ..services import enroll_user_in_course

blp = Blueprint(
    "Courses",
    "courses",
    url_prefix="/api/courses",
    description="Course CRUD, listing, and enrollment",
)


@blp.route("/")
class CourseList(MethodView):
    """
    PUBLIC_INTERFACE
    List published courses or create a new course (instructor/admin).
    """
    def get(self):
        published = request.args.get("published")
        q = Course.query
        if published is not None:
            q = q.filter_by(published=(published == "true"))
        courses = q.order_by(Course.created_at.desc()).all()
        return [
            {"id": c.id, "title": c.title, "description": c.description, "instructor_id": c.instructor_id,
             "price_cents": c.price_cents, "published": c.published}
            for c in courses
        ]

    @jwt_required()
    @require_roles(["instructor", "admin"])
    def post(self):
        data = request.get_json() or {}
        ident = get_jwt_identity()
        instructor_id = ident.get("id")
        c = Course(
            title=data.get("title", "Untitled"),
            description=data.get("description"),
            instructor_id=instructor_id,
            price_cents=int(data.get("price_cents", 0)),
            published=bool(data.get("published", False)),
        )
        db.session.add(c)
        db.session.commit()
        return {"id": c.id, "message": "Created"}, 201


@blp.route("/<int:course_id>")
class CourseDetail(MethodView):
    """
    PUBLIC_INTERFACE
    Get, update, or delete a course.
    """
    def get(self, course_id: int):
        c = Course.query.get_or_404(course_id)
        return {"id": c.id, "title": c.title, "description": c.description, "instructor_id": c.instructor_id,
                "price_cents": c.price_cents, "published": c.published}

    @jwt_required()
    @require_roles(["instructor", "admin"])
    def put(self, course_id: int):
        c = Course.query.get_or_404(course_id)
        data = request.get_json() or {}
        c.title = data.get("title", c.title)
        c.description = data.get("description", c.description)
        c.price_cents = int(data.get("price_cents", c.price_cents))
        if "published" in data:
            c.published = bool(data.get("published"))
        db.session.commit()
        return {"message": "Updated"}

    @jwt_required()
    @require_roles(["admin"])
    def delete(self, course_id: int):
        c = Course.query.get_or_404(course_id)
        db.session.delete(c)
        db.session.commit()
        return {"message": "Deleted"}


@blp.route("/<int:course_id>/enroll")
class CourseEnroll(MethodView):
    """
    PUBLIC_INTERFACE
    Enroll current user in a course.
    """
    @jwt_required()
    def post(self, course_id: int):
        ident = get_jwt_identity()
        uid = ident.get("id")
        enrollment, err = enroll_user_in_course(uid, course_id)
        if err:
            return {"message": err}, 400
        return {"message": "Enrolled", "enrollment_id": enrollment.id}, 201
