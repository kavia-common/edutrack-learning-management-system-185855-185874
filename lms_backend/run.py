from app import create_app, socketio
from app.sockets import register_socket_namespaces

app = create_app()
register_socket_namespaces()

if __name__ == "__main__":
    # Note: In production behind a WSGI/ASGI server (eventlet/gevent recommended for SocketIO).
    socketio.run(app, host="0.0.0.0", port=int(3001))
