import time
from sqlalchemy import text
from dotenv import load_dotenv

from app import create_app, socketio, db
from app.sockets import register_socket_namespaces

# Load .env before creating app (no-op if missing)
load_dotenv()

app = create_app()
register_socket_namespaces()

def _wait_for_db_preflight(max_retries: int = 15, sleep_s: float = 1.0):
    """
    Best-effort preflight DB check before binding the port to reduce early 500s.
    Non-fatal: if fails, server still starts and /health/db can be polled.
    """
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite:"):
        return
    last_err = None
    for _ in range(max_retries):
        try:
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                db.session.commit()
            return
        except Exception as e:
            last_err = e
            time.sleep(sleep_s)
    print(f"[run.py] DB preflight not ready: {last_err}")

if __name__ == "__main__":
    # Preflight wait (non-fatal)
    _wait_for_db_preflight()

    # Note: In production behind a WSGI/ASGI server (eventlet/gevent recommended for SocketIO).
    socketio.run(app, host="0.0.0.0", port=int(3001))
