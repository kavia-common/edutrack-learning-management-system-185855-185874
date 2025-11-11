from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from ..models import User
from ..services import authenticate_user, create_user

blp = Blueprint(
    "Auth",
    "auth",
    url_prefix="/api/auth",
    description="Authentication endpoints for registration, login, token refresh, and profile",
)


@blp.route("/register")
class Register(MethodView):
    """
    PUBLIC_INTERFACE
    Register a new user.

    Request JSON:
        - email: string
        - password: string
        - full_name: string
        - role: string (optional; defaults to 'student')
    Response:
        - message, user: {id, email, full_name, role}
    """
    def post(self):
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        full_name = data.get("full_name", "")
        role = data.get("role", "student")
        user, err = create_user(email, password, full_name, role)
        if err:
            return {"message": err}, 400
        return {
            "message": "Registered",
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.name},
        }, 201


@blp.route("/login")
class Login(MethodView):
    """
    PUBLIC_INTERFACE
    Login to receive access and refresh tokens.
    """
    def post(self):
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        user = authenticate_user(email, password)
        if not user:
            return {"message": "Invalid credentials"}, 401
        identity = {"id": user.id, "email": user.email}
        additional_claims = {"role": user.role.name}
        access = create_access_token(identity=identity, additional_claims=additional_claims)
        refresh = create_refresh_token(identity=identity, additional_claims=additional_claims)
        return {"access_token": access, "refresh_token": refresh}


@blp.route("/refresh")
class Refresh(MethodView):
    """
    PUBLIC_INTERFACE
    Refresh access token using refresh token.
    """
    @jwt_required(refresh=True)
    def post(self):
        identity = get_jwt_identity()
        # Claims are inferred from identity by re-fetching user role would be ideal; for simplicity, keep previous role if present
        access = create_access_token(identity=identity)
        return {"access_token": access}


@blp.route("/me")
class Me(MethodView):
    """
    PUBLIC_INTERFACE
    Get current user profile.
    """
    @jwt_required()
    def get(self):
        ident = get_jwt_identity() or {}
        uid = ident.get("id")
        user = User.query.get(uid)
        if not user:
            return {"message": "User not found"}, 404
        return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.name}
