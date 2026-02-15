"""Simple Flask application for brownfield testing."""

from flask import Flask, jsonify, request


def create_app():
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/users", methods=["GET"])
    def list_users():
        from models import get_all_users
        users = get_all_users()
        return jsonify({"users": users})

    @app.route("/users", methods=["POST"])
    def create_user():
        data = request.get_json()
        if not data or "name" not in data or "email" not in data:
            return jsonify({"error": "name and email required"}), 400
        from models import add_user
        user = add_user(data["name"], data["email"])
        return jsonify(user), 201

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
