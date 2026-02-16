import pytest
from flask import Flask
from src.api.user_routes import user_bp
from src.services.user_service import get_repo


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(user_bp)
    return app


@pytest.fixture()
def app():
    app = create_app()
    yield app
    get_repo().reset()


@pytest.fixture()
def client(app):
    return app.test_client()
