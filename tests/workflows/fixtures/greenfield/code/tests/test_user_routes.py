import json


def test_register_returns_201(client):
    resp = client.post(
        "/users/register",
        data=json.dumps({"email": "new@example.com", "password": "Str0ngPass"}),
        content_type="application/json",
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["email"] == "new@example.com"
    assert "id" in body


def test_duplicate_email_returns_409(client):
    payload = json.dumps({"email": "dup@example.com", "password": "Str0ngPass"})
    client.post("/users/register", data=payload, content_type="application/json")
    resp = client.post("/users/register", data=payload, content_type="application/json")
    assert resp.status_code == 409


def test_missing_fields_returns_422(client):
    resp = client.post(
        "/users/register",
        data=json.dumps({"email": "only@example.com"}),
        content_type="application/json",
    )
    assert resp.status_code == 422
    body = resp.get_json()
    assert "error" in body
