from datetime import timedelta
import pytest
import jwt
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    password = "SuperSecurePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt prefix
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_token_creation_and_decoding():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    claims = {"email": "user@quantweave.test", "role": "analyst"}
    token = create_access_token(subject=user_id, claims=claims)

    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == "user@quantweave.test"
    assert payload["role"] == "analyst"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    # Create token that expired 1 hour ago
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(hours=-1)
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_refresh_token_type():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_refresh_token(subject=user_id)
    payload = decode_token(token)
    assert payload["type"] == "refresh"
