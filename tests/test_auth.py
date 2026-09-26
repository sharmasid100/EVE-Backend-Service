def test_signup_and_login(client):
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "new@example.com", "password": "password123", "full_name": "New User"},
    )
    assert signup.status_code == 201
    body = signup.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body
    assert "password" not in body

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]


def test_signup_validation(client):
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "bad", "password": "short", "full_name": "X"},
    )
    assert resp.status_code == 422


def test_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123", "full_name": "Dup"}
    assert client.post("/api/v1/auth/signup", json=payload).status_code == 201
    assert client.post("/api/v1/auth/signup", json=payload).status_code == 409


def test_missing_token(client):
    resp = client.get("/api/v1/centres")
    assert resp.status_code == 401
