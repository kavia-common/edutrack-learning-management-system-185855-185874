from functools import wraps
from typing import Iterable

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash


# PUBLIC_INTERFACE
def hash_password(plain: str) -> str:
    """Hash a plaintext password using werkzeug security."""
    return generate_password_hash(plain)


# PUBLIC_INTERFACE
def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    return check_password_hash(hashed, plain)


# PUBLIC_INTERFACE
def require_roles(roles: Iterable[str]):
    """
    Decorator to require one of the specified roles to access a route.
    Usage:
        @app.route('/admin')
        @require_roles(['admin'])
        def admin_view(): ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt() or {}
            role = claims.get("role")
            if role not in roles:
                return jsonify({"message": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
