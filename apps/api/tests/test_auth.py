from datetime import timedelta
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User


def test_register_user_success(client: TestClient):
    payload = {
        "name": "Jane Trader",
        "email": "jane@quantweave.test",
        "password": "ValidPassword987!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "jane@quantweave.test"
    assert data["user"]["name"] == "Jane Trader"
    assert data["user"]["role"] == "user"
    assert "id" in data["user"]

    # Verify HttpOnly cookie was set
    assert settings.cookie_name in response.cookies
    assert response.cookies[settings.cookie_name] == data["access_token"]


def test_register_duplicate_email(client: TestClient, test_user: User):
    payload = {
        "name": "Duplicate Trader",
        "email": test_user.email,  # already exists
        "password": "ValidPassword987!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_register_validation_short_password(client: TestClient):
    payload = {
        "name": "Short Pwd",
        "email": "short@quantweave.test",
        "password": "short",  # < 8 chars
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_validation_invalid_email(client: TestClient):
    payload = {
        "name": "Bad Email",
        "email": "not-an-email",
        "password": "ValidPassword987!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success(client: TestClient, test_user: User):
    payload = {
        "email": test_user.email,
        "password": "StrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == str(test_user.id)
    assert data["user"]["email"] == test_user.email

    # Check cookie
    assert settings.cookie_name in response.cookies


def test_login_wrong_password(client: TestClient, test_user: User):
    payload = {
        "email": test_user.email,
        "password": "IncorrectPassword!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_email(client: TestClient):
    payload = {
        "email": "ghost@quantweave.test",
        "password": "SomePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_logout(client: TestClient, test_user: User):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_get_current_user_with_bearer_token(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


def test_get_current_user_with_cookie(client: TestClient, test_user: User, test_user_token: str):
    client.cookies.set(settings.cookie_name, test_user_token)
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email


def test_get_current_user_unauthenticated(client: TestClient):
    client.cookies.clear()
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()


def test_get_current_user_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer not-a-valid-jwt-token"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


def test_get_current_user_expired_token(client: TestClient, test_user: User):
    expired_token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(hours=-2),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


def test_auth_me_alias_route(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(test_user.id)


def test_update_current_user_profile(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    payload = {"name": "Senior Quantitative Researcher"}
    response = client.patch("/api/v1/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Senior Quantitative Researcher"
    assert data["email"] == test_user.email


def test_change_current_user_password(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # 1. Invalid current password
    bad_payload = {
        "current_password": "WrongPassword999!",
        "new_password": "BrandNewPassword123!",
    }
    bad_res = client.post("/api/v1/users/change-password", json=bad_payload, headers=headers)
    assert bad_res.status_code == 400
    assert "verification failed" in bad_res.json()["detail"].lower()

    # 2. Valid current password
    good_payload = {
        "current_password": "StrongPassword123!",
        "new_password": "BrandNewPassword123!",
    }
    good_res = client.post("/api/v1/users/change-password", json=good_payload, headers=headers)
    assert good_res.status_code == 200
    assert "successfully" in good_res.json()["message"].lower()

    # 3. Verify new password allows login
    login_res = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "BrandNewPassword123!",
    })
    assert login_res.status_code == 200

