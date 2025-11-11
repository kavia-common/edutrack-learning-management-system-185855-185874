from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint(
    "WebSocketHelp",
    "websocket_help",
    url_prefix="/api/ws",
    description="Documentation/help for WebSocket usage (Flask-SocketIO namespace '/notifications')",
)


@blp.route("/docs")
class WebSocketDocs(MethodView):
    """
    PUBLIC_INTERFACE
    Provide help instructions for connecting to WebSocket notifications.
    """
    def get(self):
        return {
            "namespace": "/notifications",
            "summary": "Connect via Socket.IO to receive real-time notifications.",
            "usage": "Use Socket.IO client and connect to the backend URL, namespace '/notifications'. Listen for 'notification' events.",
            "events": {"notification": {"payload": {"id": "int", "message": "string", "created_at": "ISO"}}},
        }
