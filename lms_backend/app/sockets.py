from flask_socketio import Namespace, emit
from . import socketio


class NotificationsNamespace(Namespace):
    """Socket.IO namespace for real-time notifications at /notifications."""
    def on_connect(self):
        emit("connected", {"message": "Connected to notifications"})
    def on_disconnect(self):
        pass


# PUBLIC_INTERFACE
def register_socket_namespaces():
    """Register Socket.IO namespaces with the global socketio instance."""
    socketio.on_namespace(NotificationsNamespace("/notifications"))
