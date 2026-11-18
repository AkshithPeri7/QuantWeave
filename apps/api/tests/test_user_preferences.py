import uuid
from fastapi.testclient import TestClient
from app.models.user import User


def test_get_default_user_preferences(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Unauthenticated request returns 401
    unauth = client.get("/api/v1/users/me/preferences")
    assert unauth.status_code == 401

    # Authenticated request returns default preferences
    res = client.get("/api/v1/users/me/preferences", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["theme"] == "signal-loom"
    assert data["avatar_preset"] == "loom"
    assert data["color_mode"] == "system"
    assert data["reduced_motion"] is False


def test_update_user_preferences_success(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Update theme to daybreak and avatar to aqua
    update_payload = {
        "theme": "daybreak",
        "avatar_preset": "aqua",
        "color_mode": "light",
        "reduced_motion": True,
    }
    res = client.patch("/api/v1/users/me/preferences", json=update_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["theme"] == "daybreak"
    assert data["avatar_preset"] == "aqua"
    assert data["color_mode"] == "light"
    assert data["reduced_motion"] is True

    # Confirm persistence with a fresh GET
    get_res = client.get("/api/v1/users/me/preferences", headers=headers)
    assert get_res.status_code == 200
    persisted = get_res.json()
    assert persisted["theme"] == "daybreak"
    assert persisted["avatar_preset"] == "aqua"
    assert persisted["color_mode"] == "light"
    assert persisted["reduced_motion"] is True


def test_update_user_preferences_validation_errors(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Invalid theme
    bad_theme = client.patch(
        "/api/v1/users/me/preferences",
        json={"theme": "unsupported-retro-neon"},
        headers=headers,
    )
    assert bad_theme.status_code == 422

    # Invalid avatar preset
    bad_avatar = client.patch(
        "/api/v1/users/me/preferences",
        json={"avatar_preset": "invalid-preset-xyz"},
        headers=headers,
    )
    assert bad_avatar.status_code == 422

    # Invalid color mode
    bad_mode = client.patch(
        "/api/v1/users/me/preferences",
        json={"color_mode": "rainbow"},
        headers=headers,
    )
    assert bad_mode.status_code == 422


def test_cross_user_preferences_isolation(client: TestClient, test_user: User, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    client.cookies.clear()

    # Set preferences for User 1
    client.patch(
        "/api/v1/users/me/preferences",
        json={"theme": "nebula", "avatar_preset": "violet"},
        headers=headers,
    )

    # Register User 2
    u2_email = f"user2_{uuid.uuid4().hex[:6]}@quantweave.test"
    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Second User", "email": u2_email, "password": "User2Password123!"},
    )
    assert reg.status_code == 201
    u2_token = reg.json()["access_token"]
    u2_headers = {"Authorization": f"Bearer {u2_token}"}

    # User 2 should have independent default preferences
    u2_res = client.get("/api/v1/users/me/preferences", headers=u2_headers)
    assert u2_res.status_code == 200
    assert u2_res.json()["theme"] == "signal-loom"
    assert u2_res.json()["avatar_preset"] == "loom"

    # User 2 changes to oceanic
    client.patch(
        "/api/v1/users/me/preferences",
        json={"theme": "oceanic", "avatar_preset": "emerald"},
        headers=u2_headers,
    )

    # Clear cookies so client uses User 1's Bearer header
    client.cookies.clear()

    # User 1's preferences remain nebula/violet
    u1_res = client.get("/api/v1/users/me/preferences", headers=headers)
    assert u1_res.json()["theme"] == "nebula"
    assert u1_res.json()["avatar_preset"] == "violet"
