def test_register(client):
    r = client.post("/api/auth/register", json={
        "username": "newuser", "email": "new@example.com",
        "password": "pass1234", "full_name": "New User"
    })
    assert r.status_code == 201
    data = r.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_email(client, user):
    r = client.post("/api/auth/register", json={
        "username": "other", "email": "test@example.com", "password": "pass1234"
    })
    assert r.status_code == 409


def test_register_short_password(client):
    r = client.post("/api/auth/register", json={
        "username": "newu", "email": "short@example.com", "password": "abc"
    })
    assert r.status_code == 400


def test_login_success(client, user):
    r = client.post("/api/auth/login", json={"email": "test@example.com", "password": "testpass123"})
    assert r.status_code == 200
    assert "access_token" in r.get_json()


def test_login_wrong_password(client, user):
    r = client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_get_me(client, user, auth):
    r = client.get("/api/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.get_json()["email"] == "test@example.com"


def test_get_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_update_me(client, user, auth):
    r = client.put("/api/auth/me", json={"full_name": "Updated Name"}, headers=auth)
    assert r.status_code == 200
    assert r.get_json()["full_name"] == "Updated Name"


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"
