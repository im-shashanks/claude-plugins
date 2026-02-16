from flask import Blueprint, request, jsonify
from src.services.user_service import register_user, DuplicateEmailError, WeakPasswordError

user_bp = Blueprint("users", __name__, url_prefix="/users")


@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 422

    try:
        user = register_user(email, password)
    except DuplicateEmailError as exc:
        return jsonify({"error": str(exc)}), 409
    except WeakPasswordError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"id": user.id, "email": user.email}), 201
