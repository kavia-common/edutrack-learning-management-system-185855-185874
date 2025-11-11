from flask_socketio import Namespace, emit
from . import socketio


class NotificationsNamespace(Namespace):
    def on_connect(self):
        emit("connected", {"message": "Connected to notifications"})
    def on_disconnect(self):
        pass


# PUBLIC_INTERFACE
def register_socket_namespaces():
    """Register namespaces with the global socketio instance."""
    socketio.on_namespace(NotificationsNamespace("/notifications"))
