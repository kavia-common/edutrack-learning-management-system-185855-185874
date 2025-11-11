from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import Notification
from .. import db
from ..services import record_notification

blp = Blueprint(
    "Notifications",
    "notifications",
    url_prefix="/api/notifications",
    description="Notification endpoints for listing and creating notifications",
)


@blp.route("/")
class NotificationsList(MethodView):
    """
    PUBLIC_INTERFACE
    List or create notifications for the current user.
    GET: List notifications for current user.
    POST: Create a notification for current user (dev/testing utility).
      Body: { "message": "string" }
    """
    @jwt_required()
    def get(self):
        ident = get_jwt_identity() or {}
        uid = ident.get("id")
        notifs = Notification.query.filter_by(user_id=uid).order_by(Notification.created_at.desc()).all()
        return [
            {
                "id": n.id,
                "message": n.message,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ]

    @jwt_required()
    def post(self):
        ident = get_jwt_identity() or {}
        uid = ident.get("id")
        data = request.get_json() or {}
        msg = data.get("message", "").strip()
        if not msg:
            return {"message": "message is required"}, 400
        notif = record_notification(uid, msg)
        return {
            "id": notif.id,
            "message": notif.message,
            "read": notif.read,
            "created_at": notif.created_at.isoformat(),
        }, 201


@blp.route("/<int:notification_id>/read")
class NotificationRead(MethodView):
    """
    PUBLIC_INTERFACE
    Mark a notification as read.
    """
    @jwt_required()
    def post(self, notification_id: int):
        ident = get_jwt_identity() or {}
        uid = ident.get("id")
        notif = Notification.query.get_or_404(notification_id)
        if notif.user_id != uid:
            return {"message": "Not found"}, 404
        notif.read = True
        db.session.commit()
        return {"message": "Marked as read"}
