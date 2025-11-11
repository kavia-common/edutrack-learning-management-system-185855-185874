from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from ..models import User
from .. import db
from ..security import require_roles

blp = Blueprint(
    "Users",
    "users",
    url_prefix="/api/users",
    description="User management endpoints",
)


@blp.route("/")
class UsersList(MethodView):
    """
    PUBLIC_INTERFACE
    List users (admin only).
    """
    @jwt_required()
    @require_roles(["admin"])
    def get(self):
        users = User.query.all()
        return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.name} for u in users]


@blp.route("/<int:user_id>")
class UserDetail(MethodView):
    """
    PUBLIC_INTERFACE
    Get or delete a user (admin only).
    """
    @jwt_required()
    @require_roles(["admin"])
    def get(self, user_id: int):
        u = User.query.get_or_404(user_id)
        return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.name}

    @jwt_required()
    @require_roles(["admin"])
    def delete(self, user_id: int):
        u = User.query.get_or_404(user_id)
        db.session.delete(u)
        db.session.commit()
        return {"message": "Deleted"}
