"""Tests for the Flask application."""

import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import create_app
import models


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        models.reset()
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_create_user(client):
    resp = client.post("/users", json={"name": "Alice", "email": "alice@test.com"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Alice"
    assert data["id"] == 1


def test_create_user_missing_fields(client):
    resp = client.post("/users", json={"name": "Bob"})
    assert resp.status_code == 400
